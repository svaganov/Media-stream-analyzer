"""Tests for native libsrt integration."""
import pytest
import ctypes
from unittest.mock import Mock, patch, MagicMock

from backend.libsrt_native import (
    LibSRTNative, SRTNativeStats, SRT_SOCKOPT, SRT_SOCKSTATUS,
    CStats, get_srt_lib
)


class TestLibSRTNative:
    """Test native SRT library wrapper."""

    def test_singleton(self):
        lib1 = get_srt_lib()
        lib2 = get_srt_lib()
        assert lib1 is lib2

    def test_stats_parsing(self):
        """Test parsing of C stats structure."""
        lib = LibSRTNative.__new__(LibSRTNative)
        lib._lib = Mock()

        # Create mock C stats
        c_stats = CStats()
        c_stats.msRTT = 24.5
        c_stats.mbpsBandwidth = 52.0
        c_stats.mbpsMaxBW = 100.0
        c_stats.pktRecvTotal = 10000
        c_stats.pktRcvLossTotal = 50
        c_stats.pktRcvDropTotal = 25
        c_stats.byteAvailRcvBuf = 50000
        c_stats.msRcvBuf = 80
        c_stats.msRcvTsbPdDelay = 120
        c_stats.pktFlightSize = 10
        c_stats.pktCongestionWindow = 100

        stats = lib._parse_stats(c_stats)

        assert stats.rtt_ms == 24.5
        assert stats.bandwidth_mbps == 52.0
        assert stats.max_bw_mbps == 100.0
        assert stats.pkt_recv_total == 10000
        assert stats.loss_rate_percent == 0.5  # 50/10000 * 100
        assert stats.drop_rate_percent == 0.25  # 25/10000 * 100

    def test_loss_rate_zero_packets(self):
        """Test loss rate with zero packets."""
        stats = SRTNativeStats()
        assert stats.loss_rate_percent == 0.0
        assert stats.drop_rate_percent == 0.0

    def test_recv_rate_calculation(self):
        """Test receive rate calculation."""
        stats = SRTNativeStats(byte_recv=1_000_000)  # 1 MB
        # 1 MB * 8 = 8 Mb = 8 Mbps
        assert stats.recv_rate_mbps == 8.0

    def test_stats_to_dict(self):
        """Test stats serialization."""
        stats = SRTNativeStats(
            rtt_ms=24.5,
            bandwidth_mbps=52.0,
            pkt_recv_total=10000,
            pkt_rcv_loss_total=50
        )

        data = stats.to_dict()
        assert data["rtt_ms"] == 24.5
        assert data["bandwidth_mbps"] == 52.0
        assert data["loss_rate_percent"] == 0.5
        assert "pkt_flight_size" in data


class TestSRTConstants:
    """Test SRT constants."""

    def test_sockopt_values(self):
        assert SRT_SOCKOPT.SRTO_LATENCY == 23
        assert SRT_SOCKOPT.SRTO_MAXBW == 16
        assert SRT_SOCKOPT.SRTO_PASSPHRASE == 27

    def test_status_values(self):
        assert SRT_SOCKSTATUS.SRTS_CONNECTED == 5
        assert SRT_SOCKSTATUS.SRTS_BROKEN == 6
