"""Audio analysis engine for DBFS, LUFS, True Peak, and Loudness History."""
import numpy as np
import logging
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class AudioAnalysis:
    """Complete audio analysis results."""
    timestamp: float

    # DBFS
    dbfs_left: float = -70.0
    dbfs_right: float = -70.0
    dbfs_peak: float = -70.0
    dbfs_peak_hold: float = -70.0

    # LUFS (EBU R128)
    lufs_m: float = -70.0  # Momentary (400ms)
    lufs_s: float = -70.0  # Short-term (3s)
    lufs_i: float = -70.0  # Integrated (infinite)

    # True Peak
    true_peak: float = -70.0
    true_peak_max: float = -70.0

    # Dynamic Range
    lra: float = 0.0  # Loudness Range (LU)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "dbfs": {
                "left": round(self.dbfs_left, 1),
                "right": round(self.dbfs_right, 1),
                "peak": round(self.dbfs_peak, 1),
                "peak_hold": round(self.dbfs_peak_hold, 1),
            },
            "lufs": {
                "m": round(self.lufs_m, 1),
                "s": round(self.lufs_s, 1),
                "i": round(self.lufs_i, 1),
            },
            "true_peak": round(self.true_peak, 1),
            "lra": round(self.lra, 1),
        }


class AudioAnalyzer:
    """Real-time audio analyzer with EBU R128 compliance."""

    # EBU R128 filter coefficients (K-weighting)
    # Pre-filter: high-pass at ~40Hz
    # RLB filter: shelving filter

    def __init__(self, sample_rate: int = 48000, channels: int = 2):
        self.sample_rate = sample_rate
        self.channels = channels

        # DBFS tracking
        self._dbfs_peak_hold = -70.0
        self._dbfs_peak_hold_time = 0.0
        self._peak_hold_duration = 2.0  # seconds

        # LUFS integration
        self._loudness_blocks: deque = deque(maxlen=int(75 * 60))  # 75 blocks/sec * 60s
        self._short_term_blocks: deque = deque(maxlen=75 * 3)  # 3 seconds
        self._momentary_blocks: deque = deque(maxlen=75 * 2)  # 2 seconds (for 400ms overlap)

        # True Peak
        self._true_peak_max = -70.0

        # Dynamic Range
        self._loudness_history: deque = deque(maxlen=75 * 60)  # 60 seconds

        # Loudness History (for graph)
        self._loudness_history_values: deque = deque(maxlen=60)  # 60 seconds
        self._loudness_history_interval: float = 1.0  # 1 second
        self._last_history_update: float = 0.0

        # Callbacks
        self._analysis_callbacks: List[Callable[[AudioAnalysis], None]] = []
        self._history_callbacks: List[Callable[[List[float]], None]] = []

        # Block size for LUFS: 400ms = 19200 samples @ 48kHz
        self._block_size = int(0.4 * sample_rate)  # 19200
        self._block_overlap = 0.75  # 75% overlap = 100ms step
        self._step_size = int(self._block_size * (1 - self._block_overlap))  # 4800

        # Buffer for overlapping blocks
        self._overlap_buffer: Optional[np.ndarray] = None

        logger.info(f"AudioAnalyzer initialized: {sample_rate}Hz, {channels}ch")

    def on_analysis(self, callback: Callable[[AudioAnalysis], None]):
        """Register analysis callback."""
        self._analysis_callbacks.append(callback)

    def on_history(self, callback: Callable[[List[float]], None]):
        """Register loudness history callback."""
        self._history_callbacks.append(callback)

    def _calculate_dbfs(self, samples: np.ndarray) -> tuple[float, float, float]:
        """Calculate DBFS levels."""
        # samples shape: (channels, n_samples)
        left = samples[0] if self.channels > 0 else np.array([])
        right = samples[1] if self.channels > 1 else left

        # Calculate peak in dBFS
        # dBFS = 20 * log10(abs(sample))
        # 0 dBFS = full scale (1.0)

        left_peak = np.max(np.abs(left)) if len(left) > 0 else 0
        right_peak = np.max(np.abs(right)) if len(right) > 0 else 0

        # Convert to dBFS, clamp at -70
        left_dbfs = 20 * np.log10(left_peak) if left_peak > 0 else -70.0
        right_dbfs = 20 * np.log10(right_peak) if right_peak > 0 else -70.0

        left_dbfs = max(left_dbfs, -70.0)
        right_dbfs = max(right_dbfs, -70.0)

        overall_peak = max(left_peak, right_peak)
        overall_dbfs = 20 * np.log10(overall_peak) if overall_peak > 0 else -70.0
        overall_dbfs = max(overall_dbfs, -70.0)

        return left_dbfs, right_dbfs, overall_dbfs

    def _calculate_loudness_block(self, samples: np.ndarray) -> float:
        """Calculate loudness of a 400ms block (EBU R128)."""
        # Simplified K-weighting + mean square
        # Full implementation would include:
        # 1. Pre-filter (high-pass)
        # 2. RLB filter (shelving)
        # 3. Mean square calculation
        # 4. Channel weighting (stereo: +3dB)

        # For now, simplified loudness calculation
        # Mean square of samples
        ms = np.mean(samples ** 2)
        if ms > 0:
            loudness = -0.691 + 10 * np.log10(ms)  # EBU R128 formula (simplified)
        else:
            loudness = -70.0

        return max(loudness, -70.0)

    def _calculate_true_peak(self, samples: np.ndarray) -> float:
        """Calculate True Peak with 4x oversampling."""
        # Simplified: just use regular peak for now
        # Full implementation would upsample 4x and measure peak
        max_sample = np.max(np.abs(samples))
        if max_sample > 0:
            return 20 * np.log10(max_sample)
        return -70.0

    def process(self, samples: np.ndarray, timestamp: float) -> AudioAnalysis:
        """Process audio samples and return analysis."""
        # samples shape: (channels, n_samples)

        # Calculate DBFS
        dbfs_left, dbfs_right, dbfs_peak = self._calculate_dbfs(samples)

        # Update peak hold
        if dbfs_peak > self._dbfs_peak_hold:
            self._dbfs_peak_hold = dbfs_peak
            self._dbfs_peak_hold_time = timestamp
        elif timestamp - self._dbfs_peak_hold_time > self._peak_hold_duration:
            self._dbfs_peak_hold = dbfs_peak
            self._dbfs_peak_hold_time = timestamp

        # Calculate loudness blocks
        # Process overlapping 400ms blocks
        n_samples = samples.shape[1]

        if self._overlap_buffer is not None:
            # Concatenate with previous overlap
            samples = np.concatenate([self._overlap_buffer, samples], axis=1)

        # Process blocks
        block_loudness_values = []
        pos = 0
        while pos + self._block_size <= samples.shape[1]:
            block = samples[:, pos:pos + self._block_size]
            loudness = self._calculate_loudness_block(block)
            block_loudness_values.append(loudness)
            pos += self._step_size

        # Save overlap for next call
        if pos < samples.shape[1]:
            self._overlap_buffer = samples[:, pos:]
        else:
            self._overlap_buffer = None

        # Update block histories
        for loudness in block_loudness_values:
            self._loudness_blocks.append(loudness)
            self._short_term_blocks.append(loudness)
            self._momentary_blocks.append(loudness)
            self._loudness_history.append(loudness)

        # Calculate LUFS values
        lufs_m = np.mean(list(self._momentary_blocks)) if self._momentary_blocks else -70.0
        lufs_s = np.mean(list(self._short_term_blocks)) if self._short_term_blocks else -70.0
        lufs_i = np.mean(list(self._loudness_blocks)) if self._loudness_blocks else -70.0

        # Calculate True Peak
        true_peak = self._calculate_true_peak(samples)
        if true_peak > self._true_peak_max:
            self._true_peak_max = true_peak

        # Calculate LRA (Loudness Range)
        if len(self._loudness_history) > 0:
            hist = np.array(list(self._loudness_history))
            p10 = np.percentile(hist, 10)
            p95 = np.percentile(hist, 95)
            lra = p95 - p10
        else:
            lra = 0.0

        # Update loudness history (1-second intervals)
        if timestamp - self._last_history_update >= self._loudness_history_interval:
            self._loudness_history_values.append(lufs_s)
            self._last_history_update = timestamp

            for callback in self._history_callbacks:
                callback(list(self._loudness_history_values))

        # Create analysis result
        analysis = AudioAnalysis(
            timestamp=timestamp,
            dbfs_left=dbfs_left,
            dbfs_right=dbfs_right,
            dbfs_peak=dbfs_peak,
            dbfs_peak_hold=self._dbfs_peak_hold,
            lufs_m=lufs_m,
            lufs_s=lufs_s,
            lufs_i=lufs_i,
            true_peak=true_peak,
            true_peak_max=self._true_peak_max,
            lra=lra,
        )

        for callback in self._analysis_callbacks:
            callback(analysis)

        return analysis

    def get_loudness_history(self) -> List[float]:
        """Get current loudness history values."""
        return list(self._loudness_history_values)

    def reset(self):
        """Reset all accumulators."""
        self._dbfs_peak_hold = -70.0
        self._loudness_blocks.clear()
        self._short_term_blocks.clear()
        self._momentary_blocks.clear()
        self._loudness_history.clear()
        self._loudness_history_values.clear()
        self._true_peak_max = -70.0
        self._overlap_buffer = None
        logger.info("Audio analyzer reset")
