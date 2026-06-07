"""Tests for alert manager."""
import pytest
import time
from unittest.mock import Mock

from backend.alert_manager import (
    AlertManager, AlertThreshold, Alert, AlertSeverity, AlertType
)


class TestAlertManager:
    """Test alert manager."""

    @pytest.fixture
    def manager(self):
        thresholds = AlertThreshold(
            rtt_warning_ms=50.0,
            rtt_critical_ms=200.0,
            loss_warning_percent=0.1,
            loss_critical_percent=1.0,
            cooldown_seconds=0.1  # Short cooldown for testing
        )
        return AlertManager(thresholds)

    def test_init(self, manager):
        assert manager.thresholds.rtt_warning_ms == 50.0
        assert len(manager.get_active_alerts()) == 0

    def test_rtt_warning(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 75.0, "loss_rate_percent": 0, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)

        callback.assert_called_once()
        alert = callback.call_args[0][0]
        assert alert.severity == "WARNING"
        assert "RTT high" in alert.message
        assert alert.value == 75.0

    def test_rtt_critical(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 250.0, "loss_rate_percent": 0, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)

        alert = callback.call_args[0][0]
        assert alert.severity == "CRITICAL"
        assert "RTT critical" in alert.message

    def test_loss_warning(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 20.0, "loss_rate_percent": 0.5, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)

        alert = callback.call_args[0][0]
        assert alert.severity == "WARNING"
        assert "Packet loss" in alert.message

    def test_loss_critical(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 20.0, "loss_rate_percent": 2.0, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)

        alert = callback.call_args[0][0]
        assert alert.severity == "CRITICAL"

    def test_buffer_low(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 20.0, "loss_rate_percent": 0, "buffer_health": 5.0, "state": "connected"}
        manager.check_srt_stats(stats)

        alert = callback.call_args[0][0]
        assert "Buffer critical" in alert.message

    def test_disconnected(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 0, "loss_rate_percent": 0, "buffer_health": 0, "state": "disconnected"}
        manager.check_srt_stats(stats)

        alert = callback.call_args[0][0]
        assert alert.severity == "ERROR"
        assert "connection lost" in alert.message

    def test_audio_clipping(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        analysis = {
            "dbfs": {"left": -0.1, "right": -0.2, "peak": -0.1},
            "lufs": {"m": -20, "s": -20, "i": -23},
            "true_peak": -0.1
        }
        manager.check_audio_analysis(analysis)

        alert = callback.call_args[0][0]
        assert "clipping" in alert.message

    def test_audio_silence(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        analysis = {
            "dbfs": {"left": -65, "right": -65, "peak": -65},
            "lufs": {"m": -65, "s": -65, "i": -65},
            "true_peak": -65
        }

        # First call starts silence timer
        manager.check_audio_analysis(analysis)
        assert callback.call_count == 0  # Not yet alerted (duration not reached)

        # Wait for silence duration
        time.sleep(0.15)
        manager.check_audio_analysis(analysis)

        alert = callback.call_args[0][0]
        assert "silence" in alert.message

    def test_cooldown(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        # First alert
        stats = {"rtt_ms": 100, "loss_rate_percent": 0, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)
        assert callback.call_count == 1

        # Same alert immediately — should be blocked by cooldown
        manager.check_srt_stats(stats)
        assert callback.call_count == 1  # Still 1

        # Wait for cooldown
        time.sleep(0.15)
        manager.check_srt_stats(stats)
        assert callback.call_count == 2  # Now 2

    def test_resolve_alert(self, manager):
        alert_callback = Mock()
        resolve_callback = Mock()
        manager.on_alert(alert_callback)
        manager.on_resolve(resolve_callback)

        # Trigger alert
        stats = {"rtt_ms": 100, "loss_rate_percent": 0, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)
        assert len(manager.get_active_alerts()) == 1

        # Resolve by going back to normal
        stats["rtt_ms"] = 20
        manager.check_srt_stats(stats)
        assert len(manager.get_active_alerts()) == 0

        resolve_callback.assert_called_once()

    def test_acknowledge(self, manager):
        callback = Mock()
        manager.on_alert(callback)

        stats = {"rtt_ms": 100, "loss_rate_percent": 0, "buffer_health": 100, "state": "connected"}
        manager.check_srt_stats(stats)

        alert = manager.get_active_alerts()[0]
        assert alert.acknowledged is False

        manager.acknowledge_alert(alert.id)
        assert alert.acknowledged is True

    def test_get_thresholds(self, manager):
        thresholds = manager.get_thresholds_dict()
        assert "rtt_warning_ms" in thresholds
        assert "loss_critical_percent" in thresholds
        assert thresholds["rtt_warning_ms"] == 50.0

    def test_update_thresholds(self, manager):
        manager.update_thresholds(rtt_warning_ms=100.0)
        assert manager.thresholds.rtt_warning_ms == 100.0


class TestAlertThreshold:
    """Test alert threshold defaults."""

    def test_defaults(self):
        t = AlertThreshold()
        assert t.rtt_warning_ms == 100.0
        assert t.rtt_critical_ms == 500.0
        assert t.loss_warning_percent == 0.1
        assert t.loss_critical_percent == 1.0
        assert t.buffer_warning_percent == 30.0
        assert t.buffer_critical_percent == 10.0

    def test_custom(self):
        t = AlertThreshold(rtt_warning_ms=50, loss_critical_percent=5.0)
        assert t.rtt_warning_ms == 50.0
        assert t.loss_critical_percent == 5.0
        assert t.rtt_critical_ms == 500.0  # Default
