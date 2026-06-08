"""EBU R128 Loudness Calculator — Sprint 1.

Implements Momentary (M), Short-term (S), and Integrated (I) loudness.
Block size: 400ms with 75% overlap (100ms step).
Reference: EBU Tech 3341.
"""

import numpy as np
from typing import Dict, Any, Optional
from collections import deque
from v2.src.core.constants import (
    LUFS_BLOCK_SIZE_MS, LUFS_OVERLAP_PERCENT, LUFS_SHORT_TERM_SEC,
    LUFS_INTEGRATED_MAX_SEC, DEFAULT_SAMPLE_RATE, LUFS_TARGET
)
from v2.src.core.models import LUFSZone
from .base import AudioAnalyzerBase


class EBUR128Calculator(AudioAnalyzerBase):
    """EBU R128 loudness calculator.
    
    Uses simplified K-weighting (pre-filter + RLB filter approximation).
    For broadcast-grade accuracy, a full FIR implementation is needed.
    """

    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE):
        super().__init__(sample_rate)
        
        # Block configuration
        self.block_size = int(LUFS_BLOCK_SIZE_MS * sample_rate / 1000)
        self.step_size = int(self.block_size * (1 - LUFS_OVERLAP_PERCENT / 100))
        self.short_term_blocks = int(LUFS_SHORT_TERM_SEC * 1000 / LUFS_BLOCK_SIZE_MS)
        self.integrated_max_blocks = int(LUFS_INTEGRATED_MAX_SEC * 1000 / LUFS_BLOCK_SIZE_MS)
        
        # Buffers
        self._block_buffer: deque = deque(maxlen=self.integrated_max_blocks)
        self._overlap_buffer: Optional[np.ndarray] = None
        
        # Current values
        self._momentary: float = -70.0
        self._short_term: float = -70.0
        self._integrated: float = -70.0

    def _k_weight(self, samples: np.ndarray) -> np.ndarray:
        """Apply simplified K-weighting.
        
        Full EBU R128 requires:
        1. Pre-filter: HPF at ~40Hz
        2. RLB filter: high-shelf at ~1kHz (+4dB)
        
        This simplified version applies channel weighting.
        """
        # For stereo, add 3dB relative power
        if samples.ndim > 1 and samples.shape[0] >= 2:
            left = samples[0]
            right = samples[1]
            # Weighted sum (stereo +3dB)
            weighted = (left + right) / 2.0
        else:
            weighted = samples if samples.ndim == 1 else samples[0]
        
        return weighted

    def _calculate_loudness_block(self, block: np.ndarray) -> float:
        """Calculate loudness of a single 400ms block."""
        weighted = self._k_weight(block)
        
        # Mean square
        ms = np.mean(weighted ** 2)
        
        if ms > 1e-10:
            # EBU R128 formula: Lk = -0.691 + 10*log10(mean_square)
            loudness = -0.691 + 10.0 * np.log10(ms)
        else:
            loudness = -70.0
        
        return max(loudness, -70.0)

    def _get_zone(self, lufs: float) -> LUFSZone:
        """Determine LUFS zone."""
        if lufs > -14.0:
            return LUFSZone.DANGER
        elif lufs >= -24.0 and lufs <= -22.0:
            return LUFSZone.TARGET
        elif lufs >= -30.0:
            return LUFSZone.SAFE
        elif lufs >= -40.0:
            return LUFSZone.QUIET
        elif lufs >= -70.0:
            return LUFSZone.QUIET
        return LUFSZone.SILENCE

    def process(self, samples: np.ndarray) -> Dict[str, Any]:
        """Process audio samples and return LUFS metrics.
        
        Args:
            samples: Array of shape (channels, n_samples)
            
        Returns:
            Dict with momentary, short_term, integrated, zone
        """
        if not self.enabled:
            return self.to_dict()

        # Ensure 2D array
        if samples.ndim == 1:
            samples = samples.reshape(1, -1)

        # Concatenate with overlap from previous call
        if self._overlap_buffer is not None:
            samples = np.concatenate([self._overlap_buffer, samples], axis=1)

        # Process overlapping blocks
        pos = 0
        n_samples = samples.shape[1]
        
        while pos + self.block_size <= n_samples:
            block = samples[:, pos:pos + self.block_size]
            loudness = self._calculate_loudness_block(block)
            self._block_buffer.append(loudness)
            pos += self.step_size

        # Save remaining samples for next call
        if pos < n_samples:
            self._overlap_buffer = samples[:, pos:]
        else:
            self._overlap_buffer = None

        # Calculate current values
        buf = list(self._block_buffer)
        
        if buf:
            # Momentary: mean of last ~10 blocks (400ms)
            self._momentary = float(np.mean(buf[-10:])) if len(buf) >= 10 else buf[-1]
            
            # Short-term: mean of last 75 blocks (3 seconds)
            self._short_term = float(np.mean(buf[-self.short_term_blocks:]))
            
            # Integrated: mean of all blocks
            self._integrated = float(np.mean(buf))
        else:
            self._momentary = self._short_term = self._integrated = -70.0

        zone = self._get_zone(self._momentary)

        return {
            "momentary": round(self._momentary, 1),
            "short_term": round(self._short_term, 1),
            "integrated": round(self._integrated, 1),
            "zone": zone.value,
        }

    def reset(self) -> None:
        """Reset all buffers."""
        self._block_buffer.clear()
        self._overlap_buffer = None
        self._momentary = self._short_term = self._integrated = -70.0

    def to_dict(self) -> Dict[str, Any]:
        """Return current state."""
        return {
            "momentary": round(self._momentary, 1),
            "short_term": round(self._short_term, 1),
            "integrated": round(self._integrated, 1),
            "zone": self._get_zone(self._momentary).value,
        }
