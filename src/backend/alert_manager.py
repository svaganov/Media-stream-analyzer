"""Alert system for real-time stream monitoring.

Monitors SRT and audio metrics against thresholds and generates alerts.
"""
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import IntEnum
from collections import deque

logger = logging.getLogger(__name__)


class AlertSeverity(IntEnum):
    """Alert severity levels."""
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3


class AlertType(IntEnum):
    """Types of alerts."""
    SRT_RTT_HIGH = "srt_rtt_high"
    SRT_LOSS_HIGH = "srt_loss_high"
    SRT_DROP_HIGH = "srt_drop_high"
    SRT_BUFFER_LOW = "srt_buffer_low"
    SRT_LATENCY_HIGH = "srt_latency_high"
    SRT_DISCONNECTED = "srt_disconnected"
    SRT_RECONNECTED = "srt_reconnected"
    AUDIO_CLIPPING = "audio_clipping"
    AUDIO_SILENCE = "audio_silence"
    AUDIO_LOUDNESS_HIGH = "audio_loudness_high"
    AUDIO_LOUDNESS_LOW = "audio_loudness_low"
    TS_SYNC_LOSS = "ts_sync_loss"
    TS_CC_ERROR = "ts_cc_error"
    TS_PCR_ERROR = "ts_pcr_error"


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    # SRT thresholds
    rtt_warning_ms: float = 100.0
    rtt_critical_ms: float = 500.0
    loss_warning_percent: float = 0.1
    loss_critical_percent: float = 1.0
    drop_warning_percent: float = 0.05
    drop_critical_percent: float = 0.5
    buffer_warning_percent: float = 30.0
    buffer_critical_percent: float = 10.0
    latency_warning_ms: float = 500.0
    latency_critical_ms: float = 1000.0

    # Audio thresholds
    dbfs_clipping_threshold: float = -0.5
    silence_threshold_dbfs: float = -60.0
    silence_duration_seconds: float = 5.0
    loudness_high_lufs: float = -14.0
    loudness_low_lufs: float = -30.0

    # TS thresholds (Sprint 6)
    cc_error_threshold: int = 1
    pcr_jitter_threshold_ns: float = 500.0

    # Cooldown (seconds) — minimum time between repeated alerts of same type
    cooldown_seconds: float = 10.0


@dataclass
class Alert:
    """Alert instance."""
    id: str
    type: str
    severity: str
    message: str
    timestamp: float
    value: Optional[float] = None
    threshold: Optional[float] = None
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "message": self.message,
            "timestamp": self.timestamp,
            "value": self.value,
            "threshold": self.threshold,
            "acknowledged": self.acknowledged,
        }


class AlertManager:
    """Manages alert generation, tracking, and notification."""

    def __init__(self, thresholds: Optional[AlertThreshold] = None):
        self.thresholds = thresholds or AlertThreshold()

        # Alert tracking
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: deque = deque(maxlen=100)
        self._last_alert_time: Dict[str, float] = {}
        self._alert_counter: int = 0

        # State tracking for duration-based alerts
        self._silence_start_time: Optional[float] = None
        self._last_dbfs: float = -70.0
        self._last_lufs_s: float = -70.0

        # Callbacks
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._resolve_callbacks: List[Callable[[str], None]] = []

        logger.info("AlertManager initialized")

    def on_alert(self, callback: Callable[[Alert], None]):
        """Register alert callback."""
        self._alert_callbacks.append(callback)

    def on_resolve(self, callback: Callable[[str], None]):
        """Register alert resolution callback."""
        self._resolve_callbacks.append(callback)

    def _notify_alert(self, alert: Alert):
        for cb in self._alert_callbacks:
            try:
                cb(alert)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def _notify_resolve(self, alert_id: str):
        for cb in self._resolve_callbacks:
            try:
                cb(alert_id)
            except Exception as e:
                logger.error(f"Resolve callback error: {e}")

    def _generate_id(self) -> str:
        self._alert_counter += 1
        return f"alert_{self._alert_counter}_{int(time.time())}"

    def _can_alert(self, alert_type: str) -> bool:
        """Check if enough time has passed since last alert of this type."""
        last_time = self._last_alert_time.get(alert_type, 0)
        return (time.time() - last_time) >= self.thresholds.cooldown_seconds

    def _create_alert(self, alert_type: str, severity: str, message: str,
                      value: Optional[float] = None, threshold: Optional[float] = None) -> Alert:
        alert = Alert(
            id=self._generate_id(),
            type=alert_type,
            severity=severity,
            message=message,
            timestamp=time.time(),
            value=value,
            threshold=threshold
        )
        self._active_alerts[alert_type] = alert
        self._alert_history.append(alert)
        self._last_alert_time[alert_type] = time.time()
        self._notify_alert(alert)
        logger.warning(f"ALERT [{severity}] {message}")
        return alert

    def _resolve_alert(self, alert_type: str):
        """Resolve an active alert."""
        if alert_type in self._active_alerts:
            alert = self._active_alerts.pop(alert_type)
            self._notify_resolve(alert.id)
            logger.info(f"RESOLVED: {alert.message}")

    # ============ SRT ALERTS ============
    def check_srt_stats(self, stats: Dict[str, Any]):
        """Check SRT statistics against thresholds."""
        rtt = stats.get("rtt_ms", 0)
        loss = stats.get("loss_rate_percent", 0)
        drop = stats.get("drop_rate_percent", 0)
        buffer = stats.get("buffer_health", 100)
        latency = stats.get("latency_ms", 0)
        state = stats.get("state", "unknown")

        # RTT alerts
        if rtt > self.thresholds.rtt_critical_ms:
            if self._can_alert("srt_rtt_critical"):
                self._create_alert("srt_rtt_critical", "CRITICAL",
                    f"RTT critical: {rtt:.1f}ms (threshold: {self.thresholds.rtt_critical_ms}ms)",
                    rtt, self.thresholds.rtt_critical_ms)
        elif rtt > self.thresholds.rtt_warning_ms:
            if self._can_alert("srt_rtt_warning"):
                self._create_alert("srt_rtt_warning", "WARNING",
                    f"RTT high: {rtt:.1f}ms (threshold: {self.thresholds.rtt_warning_ms}ms)",
                    rtt, self.thresholds.rtt_warning_ms)
        else:
            self._resolve_alert("srt_rtt_critical")
            self._resolve_alert("srt_rtt_warning")

        # Loss alerts
        if loss > self.thresholds.loss_critical_percent:
            if self._can_alert("srt_loss_critical"):
                self._create_alert("srt_loss_critical", "CRITICAL",
                    f"Packet loss critical: {loss:.2f}% (threshold: {self.thresholds.loss_critical_percent}%)",
                    loss, self.thresholds.loss_critical_percent)
        elif loss > self.thresholds.loss_warning_percent:
            if self._can_alert("srt_loss_warning"):
                self._create_alert("srt_loss_warning", "WARNING",
                    f"Packet loss high: {loss:.2f}% (threshold: {self.thresholds.loss_warning_percent}%)",
                    loss, self.thresholds.loss_warning_percent)
        else:
            self._resolve_alert("srt_loss_critical")
            self._resolve_alert("srt_loss_warning")

        # Drop alerts
        if drop > self.thresholds.drop_critical_percent:
            if self._can_alert("srt_drop_critical"):
                self._create_alert("srt_drop_critical", "CRITICAL",
                    f"Packet drop critical: {drop:.2f}% (threshold: {self.thresholds.drop_critical_percent}%)",
                    drop, self.thresholds.drop_critical_percent)
        elif drop > self.thresholds.drop_warning_percent:
            if self._can_alert("srt_drop_warning"):
                self._create_alert("srt_drop_warning", "WARNING",
                    f"Packet drop high: {drop:.2f}% (threshold: {self.thresholds.drop_warning_percent}%)",
                    drop, self.thresholds.drop_warning_percent)
        else:
            self._resolve_alert("srt_drop_critical")
            self._resolve_alert("srt_drop_warning")

        # Buffer alerts
        if buffer < self.thresholds.buffer_critical_percent:
            if self._can_alert("srt_buffer_critical"):
                self._create_alert("srt_buffer_critical", "CRITICAL",
                    f"Buffer critical: {buffer:.1f}% (threshold: {self.thresholds.buffer_critical_percent}%)",
                    buffer, self.thresholds.buffer_critical_percent)
        elif buffer < self.thresholds.buffer_warning_percent:
            if self._can_alert("srt_buffer_warning"):
                self._create_alert("srt_buffer_warning", "WARNING",
                    f"Buffer low: {buffer:.1f}% (threshold: {self.thresholds.buffer_warning_percent}%)",
                    buffer, self.thresholds.buffer_warning_percent)
        else:
            self._resolve_alert("srt_buffer_critical")
            self._resolve_alert("srt_buffer_warning")

        # Latency alerts
        if latency > self.thresholds.latency_critical_ms:
            if self._can_alert("srt_latency_critical"):
                self._create_alert("srt_latency_critical", "CRITICAL",
                    f"Latency critical: {latency}ms (threshold: {self.thresholds.latency_critical_ms}ms)",
                    latency, self.thresholds.latency_critical_ms)
        elif latency > self.thresholds.latency_warning_ms:
            if self._can_alert("srt_latency_warning"):
                self._create_alert("srt_latency_warning", "WARNING",
                    f"Latency high: {latency}ms (threshold: {self.thresholds.latency_warning_ms}ms)",
                    latency, self.thresholds.latency_warning_ms)
        else:
            self._resolve_alert("srt_latency_critical")
            self._resolve_alert("srt_latency_warning")

        # Connection state alerts
        if state == "disconnected":
            if self._can_alert("srt_disconnected"):
                self._create_alert("srt_disconnected", "ERROR",
                    "SRT connection lost", None, None)
        else:
            self._resolve_alert("srt_disconnected")

    # ============ AUDIO ALERTS ============
    def check_audio_analysis(self, analysis: Dict[str, Any]):
        """Check audio analysis against thresholds."""
        dbfs = analysis.get("dbfs", {})
        lufs = analysis.get("lufs", {})
        true_peak = analysis.get("true_peak", -70.0)

        left_dbfs = dbfs.get("left", -70.0)
        right_dbfs = dbfs.get("right", -70.0)
        peak_dbfs = dbfs.get("peak", -70.0)
        lufs_s = lufs.get("s", -70.0)

        # Clipping alert
        if peak_dbfs > self.thresholds.dbfs_clipping_threshold:
            if self._can_alert("audio_clipping"):
                self._create_alert("audio_clipping", "ERROR",
                    f"Audio clipping detected: {peak_dbfs:.1f} dBFS",
                    peak_dbfs, self.thresholds.dbfs_clipping_threshold)
        else:
            self._resolve_alert("audio_clipping")

        # Silence detection
        avg_dbfs = (left_dbfs + right_dbfs) / 2
        if avg_dbfs < self.thresholds.silence_threshold_dbfs:
            if self._silence_start_time is None:
                self._silence_start_time = time.time()
            elif (time.time() - self._silence_start_time) >= self.thresholds.silence_duration_seconds:
                if self._can_alert("audio_silence"):
                    self._create_alert("audio_silence", "WARNING",
                        f"Audio silence detected for {self.thresholds.silence_duration_seconds}s: {avg_dbfs:.1f} dBFS",
                        avg_dbfs, self.thresholds.silence_threshold_dbfs)
        else:
            self._silence_start_time = None
            self._resolve_alert("audio_silence")

        # Loudness alerts
        if lufs_s > self.thresholds.loudness_high_lufs:
            if self._can_alert("audio_loudness_high"):
                self._create_alert("audio_loudness_high", "WARNING",
                    f"Loudness too high: {lufs_s:.1f} LUFS (target: -23 LUFS)",
                    lufs_s, self.thresholds.loudness_high_lufs)
        elif lufs_s < self.thresholds.loudness_low_lufs:
            if self._can_alert("audio_loudness_low"):
                self._create_alert("audio_loudness_low", "WARNING",
                    f"Loudness too low: {lufs_s:.1f} LUFS (target: -23 LUFS)",
                    lufs_s, self.thresholds.loudness_low_lufs)
        else:
            self._resolve_alert("audio_loudness_high")
            self._resolve_alert("audio_loudness_low")

    # ============ TS ALERTS (Sprint 6) ============
    def check_ts_stats(self, ts_stats: Dict[str, Any]):
        """Check TS statistics against thresholds (Sprint 6)."""
        cc_errors = ts_stats.get("cc_errors", 0)
        pcr_jitter = ts_stats.get("pcr_jitter_ns", 0)
        sync_loss = ts_stats.get("sync_loss", False)

        if sync_loss:
            if self._can_alert("ts_sync_loss"):
                self._create_alert("ts_sync_loss", "CRITICAL",
                    "MPEG-TS sync loss detected", None, None)
        else:
            self._resolve_alert("ts_sync_loss")

        if cc_errors > self.thresholds.cc_error_threshold:
            if self._can_alert("ts_cc_error"):
                self._create_alert("ts_cc_error", "ERROR",
                    f"Continuity counter errors: {cc_errors}",
                    cc_errors, self.thresholds.cc_error_threshold)
        else:
            self._resolve_alert("ts_cc_error")

        if pcr_jitter > self.thresholds.pcr_jitter_threshold_ns:
            if self._can_alert("ts_pcr_error"):
                self._create_alert("ts_pcr_error", "WARNING",
                    f"PCR jitter high: {pcr_jitter:.0f}ns (threshold: {self.thresholds.pcr_jitter_threshold_ns}ns)",
                    pcr_jitter, self.thresholds.pcr_jitter_threshold_ns)
        else:
            self._resolve_alert("ts_pcr_error")

    # ============ MANAGEMENT ============
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return list(self._active_alerts.values())

    def get_alert_history(self) -> List[Alert]:
        """Get alert history."""
        return list(self._alert_history)

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert by ID."""
        for alert in self._active_alerts.values():
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False

    def acknowledge_all(self):
        """Acknowledge all active alerts."""
        for alert in self._active_alerts.values():
            alert.acknowledged = True

    def clear_all(self):
        """Clear all active alerts."""
        for alert_type in list(self._active_alerts.keys()):
            self._resolve_alert(alert_type)

    def update_thresholds(self, **kwargs):
        """Update alert thresholds."""
        for key, value in kwargs.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                logger.info(f"Threshold updated: {key} = {value}")

    def get_thresholds_dict(self) -> Dict[str, float]:
        """Get current thresholds as dictionary."""
        return {
            "rtt_warning_ms": self.thresholds.rtt_warning_ms,
            "rtt_critical_ms": self.thresholds.rtt_critical_ms,
            "loss_warning_percent": self.thresholds.loss_warning_percent,
            "loss_critical_percent": self.thresholds.loss_critical_percent,
            "drop_warning_percent": self.thresholds.drop_warning_percent,
            "drop_critical_percent": self.thresholds.drop_critical_percent,
            "buffer_warning_percent": self.thresholds.buffer_warning_percent,
            "buffer_critical_percent": self.thresholds.buffer_critical_percent,
            "latency_warning_ms": self.thresholds.latency_warning_ms,
            "latency_critical_ms": self.thresholds.latency_critical_ms,
            "dbfs_clipping_threshold": self.thresholds.dbfs_clipping_threshold,
            "silence_threshold_dbfs": self.thresholds.silence_threshold_dbfs,
            "silence_duration_seconds": self.thresholds.silence_duration_seconds,
            "loudness_high_lufs": self.thresholds.loudness_high_lufs,
            "loudness_low_lufs": self.thresholds.loudness_low_lufs,
        }
