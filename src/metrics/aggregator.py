"""
Metrics Aggregator for Media Stream Analyzer

Combines data from all analyzers (EBU R128, DBFS, FFT, etc.) and manages
time window statistics. Sends aggregated data via WebSocket.
"""

import time
import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

from src.core.time_window import TimeWindowManager, TimeWindow, window_manager
from src.analyzers.audio.ebu_r128 import EBUR128Calculator
from src.analyzers.audio.dbfs_meter import DBFSMeter
from src.analyzers.audio.true_peak import TruePeakDetector
from src.analyzers.audio.fft_spectrum import FFTSpectrumAnalyzer, SpectrumData
from src.analyzers.audio.silence_detector import SilenceDetector


@dataclass
class AudioMetrics:
    """Complete audio metrics snapshot."""
    timestamp: float
    session_duration: float

    # DBFS
    dbfs_left: float
    dbfs_right: float
    dbfs_peak: float
    dbfs_zone: str
    dbfs_peak_hold: float
    dbfs_min: float
    dbfs_max: float
    dbfs_dynamic_range: float

    # True Peak
    true_peak_db: float
    true_peak_clip: bool

    # LUFS
    lufs_momentary: float
    lufs_short_term: float
    lufs_integrated: float
    lufs_zone: str
    lufs_peak_hold: float
    lufs_min: float
    lufs_max: float
    lra: float  # Loudness Range

    # Spectrum
    spectrum_peak_freq: float
    spectrum_peak_db: float
    spectrum_bands: List[float] = field(default_factory=list)

    # Bitrate & Jitter (from input)
    bitrate_instant: float
    bitrate_min: float
    bitrate_max: float
    bitrate_avg: float
    jitter_instant: float
    jitter_min: float
    jitter_max: float
    jitter_avg: float

    # Errors
    crc_total: int
    sync_total: int

    # Silence
    silence_active: bool
    silence_duration: float

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsAggregator:
    """
    Aggregates metrics from all audio analyzers and manages time windows.

    Usage:
        aggregator = MetricsAggregator()
        aggregator.process_audio_frame(pcm_data)
        metrics = aggregator.get_current_metrics()
        window_stats = aggregator.get_window_stats(TimeWindow.FIFTEEN_MINUTES)
    """

    def __init__(self, sample_rate: int = 48000, time_window: TimeWindow = TimeWindow.FIFTEEN_MINUTES):
        self.sample_rate = sample_rate
        self.time_window = time_window
        self.session_start = None

        # Analyzers
        self.ebu_r128 = EBUR128Calculator(sample_rate=sample_rate)
        self.dbfs_meter = DBFSMeter()
        self.true_peak = TruePeakDetector(sample_rate=sample_rate)
        self.fft_analyzer = FFTSpectrumAnalyzer(fft_size=1024, sample_rate=sample_rate)
        self.silence_detector = SilenceDetector(threshold_db=-60, duration_sec=1.0)

        # Time window manager
        self.window_mgr = window_manager

        # Register metrics
        self._register_metrics()

        # Current values
        self._current_metrics: Optional[AudioMetrics] = None
        self._last_update = 0

        # Error counters
        self.crc_count = 0
        self.sync_count = 0

        # Metadata
        self._metadata = {}

    def _register_metrics(self) -> None:
        """Register all metrics with time window manager."""
        metrics = [
            "dbfs_left", "dbfs_right", "dbfs_peak", "true_peak_db",
            "lufs_momentary", "lufs_short_term", "lufs_integrated",
            "bitrate", "jitter", "spectrum_peak_freq", "spectrum_peak_db"
        ]
        for metric in metrics:
            self.window_mgr.register_metric(metric)

    def start_session(self) -> None:
        """Start new analysis session."""
        self.session_start = time.time()
        self.crc_count = 0
        self.sync_count = 0
        self.reset()

    def stop_session(self) -> None:
        """Stop analysis session."""
        self.session_start = None

    def reset(self) -> None:
        """Reset all measurements."""
        self.ebu_r128.reset()
        self.dbfs_meter.reset()
        self.true_peak.reset()
        self.fft_analyzer.reset()
        self.silence_detector.reset()
        self.window_mgr.reset()
        self._current_metrics = None

        # Re-register after reset
        self._register_metrics()

    def set_time_window(self, window: TimeWindow) -> None:
        """Change active time window."""
        self.time_window = window

    def process_audio_frame(self, pcm_data: np.ndarray) -> None:
        """
        Process audio frame through all analyzers.

        Args:
            pcm_data: PCM audio data (float32, shape: [samples, channels] or [samples])
        """
        if self.session_start is None:
            return

        # Ensure stereo
        if len(pcm_data.shape) == 1:
            pcm_data = np.column_stack([pcm_data, pcm_data])

        # DBFS
        dbfs_left = self.dbfs_meter.measure(pcm_data[:, 0])
        dbfs_right = self.dbfs_meter.measure(pcm_data[:, 1])
        dbfs_peak = max(dbfs_left, dbfs_right)

        # True Peak
        tp_left = self.true_peak.measure(pcm_data[:, 0])
        tp_right = self.true_peak.measure(pcm_data[:, 1])
        true_peak = max(tp_left, tp_right)

        # EBU R128
        lufs_m = self.ebu_r128.process_momentary(pcm_data)
        lufs_s = self.ebu_r128.process_short_term()
        lufs_i = self.ebu_r128.process_integrated()

        # FFT Spectrum
        spectrum = self.fft_analyzer.process(pcm_data.flatten())

        # Silence
        silence = self.silence_detector.process(dbfs_peak)

        # Record to time windows
        self.window_mgr.record("dbfs_left", dbfs_left)
        self.window_mgr.record("dbfs_right", dbfs_right)
        self.window_mgr.record("dbfs_peak", dbfs_peak)
        self.window_mgr.record("true_peak_db", true_peak)
        self.window_mgr.record("lufs_momentary", lufs_m)
        self.window_mgr.record("lufs_short_term", lufs_s)
        self.window_mgr.record("lufs_integrated", lufs_i)

        if spectrum:
            self.window_mgr.record("spectrum_peak_freq", spectrum.peak_frequency)
            self.window_mgr.record("spectrum_peak_db", spectrum.peak_magnitude_db)

        # Build metrics snapshot
        session_duration = time.time() - self.session_start

        # Get window stats for bitrate/jitter (would come from input)
        bitrate_stats = self.window_mgr.get_stats("bitrate", self.time_window)
        jitter_stats = self.window_mgr.get_stats("jitter", self.time_window)

        # Get DBFS min/max from window
        dbfs_stats = self.window_mgr.get_stats("dbfs_peak", self.time_window)

        # Get LUFS min/max
        lufs_stats = self.window_mgr.get_stats("lufs_integrated", self.time_window)

        # Determine zones
        dbfs_zone = self._dbfs_zone(dbfs_peak)
        lufs_zone = self._lufs_zone(lufs_m)

        # Spectrum bands for display
        spectrum_bands = []
        if spectrum:
            display = self.fft_analyzer.get_display_bands(spectrum, band_count=64)
            spectrum_bands = display["magnitudes_db"]

        self._current_metrics = AudioMetrics(
            timestamp=time.time(),
            session_duration=session_duration,
            dbfs_left=dbfs_left,
            dbfs_right=dbfs_right,
            dbfs_peak=dbfs_peak,
            dbfs_zone=dbfs_zone,
            dbfs_peak_hold=self.dbfs_meter.peak_hold,
            dbfs_min=dbfs_stats.minimum if dbfs_stats.count > 0 else -99.0,
            dbfs_max=dbfs_stats.maximum if dbfs_stats.count > 0 else 0.0,
            dbfs_dynamic_range=(dbfs_stats.maximum - dbfs_stats.minimum) if dbfs_stats.count > 0 else 0.0,
            true_peak_db=true_peak,
            true_peak_clip=true_peak > -1.0,
            lufs_momentary=lufs_m,
            lufs_short_term=lufs_s,
            lufs_integrated=lufs_i,
            lufs_zone=lufs_zone,
            lufs_peak_hold=self.ebu_r128.peak_hold,
            lufs_min=lufs_stats.minimum if lufs_stats.count > 0 else -99.0,
            lufs_max=lufs_stats.maximum if lufs_stats.count > 0 else 0.0,
            lra=self.ebu_r128.loudness_range,
            spectrum_peak_freq=spectrum.peak_frequency if spectrum else 0.0,
            spectrum_peak_db=spectrum.peak_magnitude_db if spectrum else -99.0,
            spectrum_bands=spectrum_bands,
            bitrate_instant=bitrate_stats.current if bitrate_stats.count > 0 else 0.0,
            bitrate_min=bitrate_stats.minimum if bitrate_stats.count > 0 else 0.0,
            bitrate_max=bitrate_stats.maximum if bitrate_stats.count > 0 else 0.0,
            bitrate_avg=bitrate_stats.average if bitrate_stats.count > 0 else 0.0,
            jitter_instant=jitter_stats.current if jitter_stats.count > 0 else 0.0,
            jitter_min=jitter_stats.minimum if jitter_stats.count > 0 else 0.0,
            jitter_max=jitter_stats.maximum if jitter_stats.count > 0 else 0.0,
            jitter_avg=jitter_stats.average if jitter_stats.count > 0 else 0.0,
            crc_total=self.crc_count,
            sync_total=self.sync_count,
            silence_active=silence["active"],
            silence_duration=silence["duration"],
            metadata=self._metadata
        )

        self._last_update = time.time()

    def _dbfs_zone(self, db: float) -> str:
        """Determine DBFS zone per EBU/SMPTE standard."""
        if db >= -6: return "danger"
        if db >= -9: return "warning"
        if db >= -18: return "caution"
        if db >= -60: return "safe"
        if db >= -70: return "quiet"
        return "silence"

    def _lufs_zone(self, lufs: float) -> str:
        """Determine LUFS zone per EBU R128."""
        if lufs > -14: return "danger"
        if lufs > -22: return "target"
        if lufs > -30: return "safe"
        if lufs > -40: return "quiet"
        return "silence"

    def get_current_metrics(self) -> Optional[AudioMetrics]:
        """Get current metrics snapshot."""
        return self._current_metrics

    def get_window_stats(self, window: TimeWindow) -> Dict[str, Any]:
        """Get statistics for all metrics in a time window."""
        metrics = self.window_mgr.get_registered_metrics()
        return {
            metric: self.window_mgr.get_stats(metric, window)
            for metric in metrics
        }

    def get_history(self, metric_name: str, window: TimeWindow, resolution: int = 1) -> List[Dict]:
        """Get history data for charting."""
        return self.window_mgr.get_history(metric_name, window, resolution)

    def record_bitrate(self, bitrate: float) -> None:
        """Record bitrate from input."""
        self.window_mgr.record("bitrate", bitrate)

    def record_jitter(self, jitter: float) -> None:
        """Record jitter from input."""
        self.window_mgr.record("jitter", jitter)

    def record_crc(self, count: int = 1) -> None:
        """Record CRC errors."""
        self.crc_count += count

    def record_sync(self, count: int = 1) -> None:
        """Record sync losses."""
        self.sync_count += count

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update stream metadata."""
        self._metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert current metrics to dictionary for JSON/WebSocket."""
        if not self._current_metrics:
            return {}

        m = self._current_metrics
        return {
            "timestamp": m.timestamp,
            "session_duration": m.session_duration,
            "audio": {
                "level_indicator": {
                    "dbfs_left": round(m.dbfs_left, 1),
                    "dbfs_right": round(m.dbfs_right, 1),
                    "dbfs_peak": round(m.dbfs_peak, 1),
                    "dbfs_zone": m.dbfs_zone,
                    "dbfs_peak_hold": round(m.dbfs_peak_hold, 1),
                    "dbfs_min": round(m.dbfs_min, 1),
                    "dbfs_max": round(m.dbfs_max, 1),
                    "dbfs_dynamic_range": round(m.dbfs_dynamic_range, 1),
                    "true_peak_db": round(m.true_peak_db, 1),
                    "true_peak_clip": m.true_peak_clip,
                    "lufs_momentary": round(m.lufs_momentary, 1),
                    "lufs_short_term": round(m.lufs_short_term, 1),
                    "lufs_integrated": round(m.lufs_integrated, 1),
                    "lufs_zone": m.lufs_zone,
                    "lufs_peak_hold": round(m.lufs_peak_hold, 1),
                    "lufs_min": round(m.lufs_min, 1),
                    "lufs_max": round(m.lufs_max, 1),
                    "lra": round(m.lra, 1)
                },
                "spectrum": {
                    "peak_frequency": int(m.spectrum_peak_freq),
                    "peak_magnitude_db": round(m.spectrum_peak_db, 1),
                    "bands": [round(b, 1) for b in m.spectrum_bands]
                },
                "bitrate": {
                    "instant": round(m.bitrate_instant, 1),
                    "min": round(m.bitrate_min, 1),
                    "max": round(m.bitrate_max, 1),
                    "avg": round(m.bitrate_avg, 1)
                },
                "jitter": {
                    "instant": round(m.jitter_instant, 1),
                    "min": round(m.jitter_min, 1),
                    "max": round(m.jitter_max, 1),
                    "avg": round(m.jitter_avg, 1)
                },
                "errors": {
                    "crc_total": m.crc_total,
                    "sync_total": m.sync_total
                },
                "silence": {
                    "active": m.silence_active,
                    "duration": round(m.silence_duration, 1)
                }
            },
            "metadata": m.metadata
        }
