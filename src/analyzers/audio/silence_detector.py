"""
Silence Detector (Sprint 2)
Stub for Sprint 3 integration.
"""

import time
from typing import Dict


class SilenceDetector:
    """Silence detection with configurable threshold and duration."""

    def __init__(self, threshold_db: float = -60, duration_sec: float = 1.0):
        self.threshold_db = threshold_db
        self.duration_sec = duration_sec
        self._silence_start = None

    def process(self, dbfs: float) -> Dict:
        """Process level and detect silence."""
        now = time.time()

        if dbfs < self.threshold_db:
            if self._silence_start is None:
                self._silence_start = now
            duration = now - self._silence_start
            return {
                "active": duration >= self.duration_sec,
                "duration": duration
            }
        else:
            self._silence_start = None
            return {"active": False, "duration": 0.0}

    def reset(self) -> None:
        """Reset detector."""
        self._silence_start = None
