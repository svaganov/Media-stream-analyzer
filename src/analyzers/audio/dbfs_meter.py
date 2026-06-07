"""
DBFS Peak Meter (Sprint 2)
Stub for Sprint 3 integration.
"""

import numpy as np


class DBFSMeter:
    """Digital Peak Level Meter."""

    def __init__(self):
        self.peak_hold = -99.0
        self._hold_time = 0

    def measure(self, samples: np.ndarray) -> float:
        """Measure peak level in dBFS."""
        peak = np.max(np.abs(samples))
        dbfs = 20 * np.log10(peak + 1e-10)

        if dbfs > self.peak_hold:
            self.peak_hold = dbfs
            self._hold_time = 0
        else:
            self._hold_time += 1
            if self._hold_time > 100:  # ~2 seconds at 50fps
                self.peak_hold = dbfs

        return float(dbfs)

    def reset(self) -> None:
        """Reset meter."""
        self.peak_hold = -99.0
        self._hold_time = 0
