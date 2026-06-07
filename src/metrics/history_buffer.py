"""
History Buffer for Media Stream Analyzer

Optimized circular buffers for chart data (bitrate, jitter, etc.).
Supports multiple time windows with automatic downsampling.
"""

import time
import numpy as np
from typing import Dict, List, Optional, Tuple
from collections import deque
from dataclasses import dataclass


@dataclass
class ChartPoint:
    """Single point for chart display."""
    timestamp: float
    value: float

    def to_dict(self) -> Dict:
        return {"timestamp": self.timestamp, "value": self.value}


class HistoryBuffer:
    """
    Circular buffer for time-series chart data.

    Automatically manages downsampling for different time windows.
    """

    def __init__(self, max_points: int = 900):
        self.max_points = max_points
        self._buffer: deque = deque(maxlen=max_points)
        self._last_value: Optional[float] = None

    def add(self, value: float, timestamp: Optional[float] = None) -> None:
        """Add value to buffer."""
        ts = timestamp or time.time()
        self._buffer.append(ChartPoint(timestamp=ts, value=value))
        self._last_value = value

    def get_points(self, count: Optional[int] = None) -> List[ChartPoint]:
        """Get recent points."""
        if count is None:
            return list(self._buffer)
        return list(self._buffer)[-count:]

    def get_values(self) -> List[float]:
        """Get just values."""
        return [p.value for p in self._buffer]

    def get_in_window(self, window_seconds: int) -> List[ChartPoint]:
        """Get points within time window."""
        cutoff = time.time() - window_seconds
        return [p for p in self._buffer if p.timestamp >= cutoff]

    def get_downsampled(self, target_points: int = 200) -> List[ChartPoint]:
        """
        Get downsampled data for chart display.
        Uses simple averaging for buckets.
        """
        points = list(self._buffer)
        if len(points) <= target_points:
            return points

        # Calculate bucket size
        bucket_size = len(points) // target_points
        result = []

        for i in range(0, len(points), bucket_size):
            bucket = points[i:i + bucket_size]
            if bucket:
                avg_value = np.mean([p.value for p in bucket])
                avg_ts = np.mean([p.timestamp for p in bucket])
                result.append(ChartPoint(timestamp=avg_ts, value=avg_value))

        return result

    def get_stats(self) -> Dict[str, float]:
        """Get statistics for current buffer."""
        values = self.get_values()
        if not values:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "current": 0.0, "count": 0}

        arr = np.array(values)
        return {
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "avg": float(np.mean(arr)),
            "current": float(values[-1]),
            "count": len(values)
        }

    def clear(self) -> None:
        """Clear buffer."""
        self._buffer.clear()
        self._last_value = None

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def is_empty(self) -> bool:
        return len(self._buffer) == 0


class MultiWindowHistory:
    """
    Manages history buffers for multiple time windows.

    Windows: 1m (60 points), 5m (300 points), 15m (900 points), 
            30m (1800 points), 60m (3600 points)
    """

    WINDOW_CONFIG = {
        "1m": {"seconds": 60, "max_points": 60},
        "5m": {"seconds": 300, "max_points": 300},
        "15m": {"seconds": 900, "max_points": 900},
        "30m": {"seconds": 1800, "max_points": 900},  # Downsampled
        "60m": {"seconds": 3600, "max_points": 900},  # Downsampled
    }

    def __init__(self):
        # metric_name -> {window -> HistoryBuffer}
        self._buffers: Dict[str, Dict[str, HistoryBuffer]] = {}

    def register_metric(self, metric_name: str) -> None:
        """Register a new metric."""
        if metric_name in self._buffers:
            return

        self._buffers[metric_name] = {}
        for window, config in self.WINDOW_CONFIG.items():
            self._buffers[metric_name][window] = HistoryBuffer(
                max_points=config["max_points"]
            )

    def add(self, metric_name: str, value: float, timestamp: Optional[float] = None) -> None:
        """Add value to all windows for a metric."""
        if metric_name not in self._buffers:
            self.register_metric(metric_name)

        for window in self.WINDOW_CONFIG.keys():
            self._buffers[metric_name][window].add(value, timestamp)

    def get_chart_data(self, metric_name: str, window: str, 
                       max_points: int = 200) -> List[Dict]:
        """
        Get chart data for a metric and window.

        Returns:
            List of {timestamp, value} dicts
        """
        if metric_name not in self._buffers:
            return []

        if window not in self._buffers[metric_name]:
            return []

        buffer = self._buffers[metric_name][window]
        points = buffer.get_downsampled(max_points)

        return [p.to_dict() for p in points]

    def get_stats(self, metric_name: str, window: str) -> Dict[str, float]:
        """Get statistics for a metric in a window."""
        if metric_name not in self._buffers or window not in self._buffers[metric_name]:
            return {"min": 0.0, "max": 0.0, "avg": 0.0, "current": 0.0, "count": 0}

        return self._buffers[metric_name][window].get_stats()

    def reset(self, metric_name: Optional[str] = None) -> None:
        """Reset buffers."""
        if metric_name is None:
            for metric_buffers in self._buffers.values():
                for buffer in metric_buffers.values():
                    buffer.clear()
        else:
            if metric_name in self._buffers:
                for buffer in self._buffers[metric_name].values():
                    buffer.clear()

    def get_registered_metrics(self) -> List[str]:
        """Get list of registered metrics."""
        return list(self._buffers.keys())


# Predefined chart configurations
CHART_CONFIGS = {
    "bitrate": {
        "title": "Bitrate History",
        "unit": "kbps",
        "color": "#8884d8",
        "thresholds": {
            "normal": {"min": 200, "max": 300},
            "warning": {"min": 150, "max": 350}
        }
    },
    "jitter": {
        "title": "Jitter History",
        "unit": "ms",
        "color": "#ff7300",
        "thresholds": {
            "normal": {"max": 50},
            "warning": {"max": 100}
        }
    },
    "dbfs_peak": {
        "title": "Peak Level History",
        "unit": "dBFS",
        "color": "#00cc00",
        "thresholds": {
            "danger": {"min": -6},
            "warning": {"min": -9}
        }
    },
    "lufs_integrated": {
        "title": "Integrated Loudness History",
        "unit": "LUFS",
        "color": "#667eea",
        "thresholds": {
            "target": {"min": -24, "max": -22}
        }
    }
}
