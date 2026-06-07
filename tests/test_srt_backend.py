"""Tests for SRT backend."""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

from backend.srt_client import SRTClient, SRTStats


class TestSRTClient:
    """Test SRT client."""

    def test_init(self):
        client = SRTClient(host="192.168.1.100", port=9000)
        assert client.host == "192.168.1.100"
        assert client.port == 9000
        assert client.mode == "caller"

    def test_url(self):
        client = SRTClient(host="192.168.1.100", port=9000)
        assert client.url == "srt://192.168.1.100:9000"

    def test_stats_callbacks(self):
        client = SRTClient()
        callback = Mock()
        client.on_stats(callback)

        stats = SRTStats(timestamp=0, rtt=24.0, bandwidth=52.0)
        client._notify_stats(stats)

        callback.assert_called_once()

    def test_stats_to_dict(self):
        stats = SRTStats(
            timestamp=0,
            rtt=24.0,
            bandwidth=52.0,
            pkt_rcv_total=1000,
            pkt_rcv_loss=10
        )

        data = stats.to_dict()
        assert data["rtt"] == 24.0
        assert data["bandwidth"] == 52.0
        assert data["pkt_loss_rate"] == 1.0  # 10/1000 * 100


class TestSRTStats:
    """Test SRT statistics."""

    def test_loss_percent(self):
        stats = SRTStats(timestamp=0, pkt_rcv_total=1000, pkt_rcv_loss=50)
        assert stats.pkt_loss_percent == 5.0

    def test_drop_percent(self):
        stats = SRTStats(timestamp=0, pkt_rcv_total=1000, pkt_rcv_drop=25)
        assert stats.pkt_drop_percent == 2.5

    def test_buffer_health(self):
        stats = SRTStats(timestamp=0, byte_avail_rcv_buf=100000)
        assert 0 <= stats.buffer_health_percent <= 100
