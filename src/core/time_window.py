"""
Time Window Manager for Media Stream Analyzer

Manages circular buffers for different time windows (1m/5m/15m/30m/60m).
Each window stores samples with timestamps for bitrate, jitter, and other metrics.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from collections import deque
import time
import numpy as np
from enum import Enum


class TimeWindow(Enum):
    """Available time windows for metrics aggregation."""
    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    SIXTY_MINUTES = "60m"

    @property
    def seconds(self) -> int:
        mapping = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "60m": 3600,
        }
        return mapping[self.value]

    @property
    def max_samples(self) -> int:
        """Maximum samples for 1-second resolution."""
        return self.seconds  # 1 sample per second


@dataclass
class MetricSample:
    """Single metric sample with timestamp."""
    timestamp: float
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class WindowStats:
    """Statistics for a time window."""
    window: str
    count: int
    current: float
    minimum: float
    maximum: float
    average: float
    median: float
    p95: float
    p99: float
    std_dev: float
    duration_seconds: float


class CircularBuffer:
    """Thread-safe circular buffer for metric samples."""

    def __init__(self, max_size: int):
        self._buffer: deque = deque(maxlen=max_size)
        self._max_size = max_size

    def append(self, sample: MetricSample) -> None:
        """Add sample to buffer."""
        self._buffer.append(sample)

    def get_samples(self, count: Optional[int] = None) -> List[MetricSample]:
        """Get recent samples."""
        if count is None or count >= len(self._buffer):
            return list(self._buffer)
        return list(self._buffer)[-count:]

    def get_values(self, count: Optional[int] = None) -> List[float]:
        """Get just the values."""
        samples = self.get_samples(count)
        return [s.value for s in samples]

    def get_samples_in_window(self, window_seconds: int) -> List[MetricSample]:
        """Get samples within time window from now."""
        cutoff = time.time() - window_seconds
        return [s for s in self._buffer if s.timestamp >= cutoff]

    def clear(self) -> None:
        """Clear all samples."""
        self._buffer.clear()

    @property
    def size(self) -> int:
        return len(self._buffer)

    @property
    def is_full(self) -> bool:
        return len(self._buffer) >= self._max_size


class TimeWindowManager:
    """
    Manages multiple circular buffers for different time windows.

    Each metric (bitrate, jitter, dbfs, lufs, etc.) gets its own set of buffers
    per time window. This allows efficient querying of min/max/avg for any window.
    """

    def __init__(self):
        self._windows: Dict[TimeWindow, int] = {
            TimeWindow.ONE_MINUTE: 60,
            TimeWindow.FIVE_MINUTES: 300,
            TimeWindow.FIFTEEN_MINUTES: 900,
            TimeWindow.THIRTY_MINUTES: 1800,
            TimeWindow.SIXTY_MINUTES: 3600,
        }

        # metric_name -> {window -> CircularBuffer}
        self._buffers: Dict[str, Dict[str, CircularBuffer]] = {}

        # metric_name -> {window -> WindowStats (cached)}
        self._cached_stats: Dict[str, Dict[str, WindowStats]] = {}

        self._last_update: float = 0
        self._stats_cache_ttl: float = 0.5  # Cache stats for 500ms

    def register_metric(self, metric_name: str) -> None:
        """Register a new metric type. Creates buffers for all windows."""
        if metric_name in self._buffers:
            return

        self._buffers[metric_name] = {}
        self._cached_stats[metric_name] = {}

        for window, max_samples in self._windows.items():
            self._buffers[metric_name][window.value] = CircularBuffer(max_samples)
            self._cached_stats[metric_name][window.value] = None

    def record(self, metric_name: str, value: float, tags: Dict[str, str] = None) -> None:
        """Record a metric value across all time windows."""
        if metric_name not in self._buffers:
            self.register_metric(metric_name)

        sample = MetricSample(
            timestamp=time.time(),
            value=value,
            tags=tags or {}
        )

        for window in self._windows.keys():
            self._buffers[metric_name][window.value].append(sample)

        # Invalidate cache
        self._last_update = time.time()
        for window in self._windows.keys():
            self._cached_stats[metric_name][window.value] = None

    def get_stats(self, metric_name: str, window: TimeWindow) -> WindowStats:
        """Get statistics for a metric in a specific window."""
        if metric_name not in self._buffers:
            self.register_metric(metric_name)

        window_str = window.value

        # Check cache
        now = time.time()
        cached = self._cached_stats[metric_name].get(window_str)
        if cached and (now - self._last_update) < self._stats_cache_ttl:
            return cached

        # Get samples in window
        buffer = self._buffers[metric_name][window_str]
        samples = buffer.get_samples_in_window(window.seconds)
        values = [s.value for s in samples]

        if not values:
            stats = WindowStats(
                window=window_str,
                count=0,
                current=0.0,
                minimum=0.0,
                maximum=0.0,
                average=0.0,
                median=0.0,
                p95=0.0,
                p99=0.0,
                std_dev=0.0,
                duration_seconds=0.0
            )
        else:
            arr = np.array(values)
            sorted_vals = np.sort(arr)

            stats = WindowStats(
                window=window_str,
                count=len(values),
                current=values[-1] if values else 0.0,
                minimum=float(np.min(arr)),
                maximum=float(np.max(arr)),
                average=float(np.mean(arr)),
                median=float(np.median(arr)),
                p95=float(np.percentile(arr, 95)),
                p99=float(np.percentile(arr, 99)),
                std_dev=float(np.std(arr)),
                duration_seconds=window.seconds
            )

        self._cached_stats[metric_name][window_str] = stats
        return stats

    def get_all_stats(self, metric_name: str) -> Dict[str, WindowStats]:
        """Get statistics for all windows for a metric."""
        return {
            window.value: self.get_stats(metric_name, window)
            for window in TimeWindow
        }

    def get_history(self, metric_name: str, window: TimeWindow, 
                    resolution: int = 1) -> List[Dict]:
        """
        Get history data for charting.

        Args:
            metric_name: Name of the metric
            window: Time window
            resolution: Seconds per data point (default 1 = 1 second)

        Returns:
            List of {timestamp, value} dicts
        """
        if metric_name not in self._buffers:
            return []

        buffer = self._buffers[metric_name][window.value]
        samples = buffer.get_samples_in_window(window.seconds)

        if not samples:
            return []

        # Downsample if needed
        if resolution > 1:
            buckets = {}
            for s in samples:
                bucket_ts = int(s.timestamp / resolution) * resolution
                if bucket_ts not in buckets:
                    buckets[bucket_ts] = []
                buckets[bucket_ts].append(s.value)

            return [
                {"timestamp": ts, "value": float(np.mean(vals))}
                for ts, vals in sorted(buckets.items())
            ]

        return [
            {"timestamp": s.timestamp, "value": s.value}
            for s in samples
        ]

    def reset(self, metric_name: Optional[str] = None) -> None:
        """Reset buffers. If metric_name is None, reset all."""
        if metric_name is None:
            for name in self._buffers:
                for buffer in self._buffers[name].values():
                    buffer.clear()
                for window in self._windows.keys():
                    self._cached_stats[name][window.value] = None
        else:
            if metric_name in self._buffers:
                for buffer in self._buffers[metric_name].values():
                    buffer.clear()
                for window in self._windows.keys():
                    self._cached_stats[metric_name][window.value] = None

    def get_registered_metrics(self) -> List[str]:
        """Get list of registered metric names."""
        return list(self._buffers.keys())


# Singleton instance
window_manager = TimeWindowManager()
