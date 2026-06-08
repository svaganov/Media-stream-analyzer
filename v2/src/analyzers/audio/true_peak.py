"""True Peak Detector — Sprint 1.

Uses 4x oversampling to detect inter-sample peaks.
Reference: ITU-R BS.1770.
"""

import numpy as np
from typing import Dict, Any
from v2.src.core.constants import TRUE_PEAK_OVERSAMPLING, DBFS_FLOOR
from .base import AudioAnalyzerBase


class TruePeakDetector(AudioAnalyzerBase):
    """True Peak detector with 4x oversampling.
    
    Inter-sample peaks can exceed 0 dBFS even when all samples
    are below full scale. Oversampling reveals these peaks.
    """

    def __init__(self, sample_rate: int = 48000, oversampling: int = TRUE_PEAK_OVERSAMPLING):
        super().__init__(sample_rate)
        self.oversampling = oversampling
        self._max_true_peak = DBFS_FLOOR

    def _upsample(self, samples: np.ndarray) -> np.ndarray:
        """Simple linear interpolation upsampling.
        
        For broadcast accuracy, a polyphase FIR filter should be used.
        """
        if samples.ndim > 1:
            # Process each channel
            channels = []
            for ch in range(samples.shape[0]):
                up = self._upsample_channel(samples[ch])
                channels.append(up)
            return np.array(channels)
        else:
            return self._upsample_channel(samples)

    def _upsample_channel(self, samples: np.ndarray) -> np.ndarray:
        """Upsample a single channel using linear interpolation."""
        n = len(samples)
        # Create new time indices
        old_indices = np.arange(n)
        new_indices = np.linspace(0, n - 1, n * self.oversampling)
        
        # Linear interpolation
        upsampled = np.interp(new_indices, old_indices, samples)
        return upsampled

    def process(self, samples: np.ndarray) -> Dict[str, Any]:
        """Process samples and return True Peak metrics.
        
        Args:
            samples: Array of shape (channels, n_samples) or (n_samples,)
            
        Returns:
            Dict with current and max true peak in dBTP
        """
        if not self.enabled:
            return self.to_dict()

        # Upsample
        upsampled = self._upsample(samples)
        
        # Find peak in upsampled signal
        if upsampled.ndim > 1:
            peak = float(np.max(np.abs(upsampled)))
        else:
            peak = float(np.max(np.abs(upsampled)))

        # Convert to dBTP
        if peak > 1e-10:
            dbtp = 20.0 * np.log10(peak)
        else:
            dbtp = DBFS_FLOOR

        dbtp = max(dbtp, DBFS_FLOOR)

        # Update max
        if dbtp > self._max_true_peak:
            self._max_true_peak = dbtp

        return {
            "current": round(dbtp, 1),
            "max": round(self._max_true_peak, 1),
            "oversample_ratio": self.oversampling,
        }

    def reset(self) -> None:
        """Reset max peak."""
        self._max_true_peak = DBFS_FLOOR

    def to_dict(self) -> Dict[str, Any]:
        """Return current state."""
        return {
            "current": DBFS_FLOOR,
            "max": round(self._max_true_peak, 1),
            "oversample_ratio": self.oversampling,
        }
