"""
SRT Socket Statistics Collector
Based on Haivision SRT API (statistics.md) and Makito x4 Decoder metrics

References:
- SRT API Statistics: https://github.com/Haivision/srt/blob/master/docs/API/statistics.md
- Haivision Makito x4 Decoder specs
"""

import time
import dataclasses
from typing import Optional, Dict, Any, Literal
from enum import Enum


class SRTConnectionState(Enum):
    """SRT connection states matching Makito x4 display"""
    STOPPED = "STOPPED"
    CONNECTING = "CONNECTING"
    LISTENING = "LISTENING"
    STREAMING = "STREAMING"
    SECURING = "SECURING"
    SCRAMBLED = "SCRAMBLED"
    PAUSED = "PAUSED"
    BROKEN = "BROKEN"


@dataclasses.dataclass
class SRTAccumulatedStats:
    """Accumulated statistics since connection start"""
    # Time
    ms_time_stamp: int = 0  # ms since socket creation

    # Packets - Received (decoder side)
    pkt_recv_total: int = 0
    pkt_recv_unique_total: int = 0
    pkt_rcv_loss_total: int = 0
    pkt_rcv_retrans_total: int = 0
    pkt_rcv_drop_total: int = 0
    pkt_rcv_undecrypt_total: int = 0

    # Packets - Control (receiver sends ACK/NAK)
    pkt_sent_ack_total: int = 0
    pkt_sent_nak_total: int = 0

    # Bytes - Received
    byte_recv_total: int = 0
    byte_recv_unique_total: int = 0
    byte_rcv_loss_total: int = 0
    byte_rcv_drop_total: int = 0
    byte_rcv_undecrypt_total: int = 0

    # Filter stats (if SRTO_PACKETFILTER enabled)
    pkt_rcv_filter_extra_total: int = 0
    pkt_rcv_filter_supply_total: int = 0
    pkt_rcv_filter_loss_total: int = 0


@dataclasses.dataclass
class SRTIntervalStats:
    """Interval-based statistics (last measurement period)"""
    # Packet rates
    pkt_recv_unique: int = 0
    pkt_rcv_drop: int = 0
    pkt_rcv_undecrypt: int = 0
    pkt_rcv_belated: int = 0  # packets received too late
    pkt_reorder_distance: int = 0  # max out-of-order distance

    # Byte rates
    byte_recv_unique: int = 0
    byte_rcv_drop: int = 0
    byte_rcv_undecrypt: int = 0

    # Bandwidth
    mbps_recv_rate: float = 0.0  # Mbps receiving rate

    # Timing
    us_snd_duration: int = 0  # sender busy time (microseconds)


@dataclasses.dataclass
class SRTInstantStats:
    """Instantaneous statistics (current state)"""
    # Network
    ms_rtt: float = 0.0  # Round Trip Time (ms) - CRITICAL metric
    mbps_bandwidth: float = 0.0  # Estimated bandwidth (Mbps)
    mbps_max_bw: float = 0.0  # Max bandwidth limit (Mbps)

    # Buffer
    byte_avail_rcv_buf: int = 0  # Available receiver buffer space
    pkt_rcv_buf: int = 0  # Acknowledged packets in receiver buffer
    byte_rcv_buf: int = 0  # Receiver buffer in bytes
    ms_rcv_buf: float = 0.0  # Buffer timespan (ms)
    ms_rcv_tsbpd_delay: int = 0  # TSBPD delay (ms)

    # Congestion
    pkt_congestion_window: int = 0
    pkt_flight_size: int = 0  # Packets in flight

    # Reorder
    pkt_reorder_tolerance: int = 0
    pkt_rcv_avg_belated_time: float = 0.0

    # MSS
    byte_mss: int = 1500  # Maximum Segment Size


@dataclasses.dataclass
class SRTConnectionInfo:
    """Connection metadata"""
    state: SRTConnectionState = SRTConnectionState.STOPPED
    up_time_seconds: float = 0.0
    source_address: str = ""
    local_port: int = 0
    peer_latency_ms: int = 120  # SRTO_PEERLATENCY
    recv_latency_ms: int = 120  # SRTO_RCVLATENCY
    encryption: Literal["none", "aes-128", "aes-256"] = "none"
    stream_id: str = ""
    reconnections: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None


@dataclasses.dataclass
class SRTMetricsSnapshot:
    """Complete SRT metrics snapshot for WebSocket/REST API"""
    timestamp: float = 0.0
    connection: SRTConnectionInfo = dataclasses.field(default_factory=SRTConnectionInfo)
    accumulated: SRTAccumulatedStats = dataclasses.field(default_factory=SRTAccumulatedStats)
    interval: SRTIntervalStats = dataclasses.field(default_factory=SRTIntervalStats)
    instantaneous: SRTInstantStats = dataclasses.field(default_factory=SRTInstantStats)

    # Calculated metrics (derived from raw stats)
    @property
    def packet_loss_rate(self) -> float:
        """Packet loss rate percentage"""
        total = self.accumulated.pkt_recv_unique_total + self.accumulated.pkt_rcv_loss_total
        if total == 0:
            return 0.0
        return (self.accumulated.pkt_rcv_loss_total / total) * 100

    @property
    def drop_rate(self) -> float:
        """Drop rate percentage (too late / undecryptable)"""
        total = self.accumulated.pkt_recv_total
        if total == 0:
            return 0.0
        drops = self.accumulated.pkt_rcv_drop_total + self.accumulated.pkt_rcv_undecrypt_total
        return (drops / total) * 100

    @property
    def retransmission_ratio(self) -> float:
        """Ratio of retransmitted packets"""
        if self.accumulated.pkt_recv_total == 0:
            return 0.0
        return (self.accumulated.pkt_rcv_retrans_total / self.accumulated.pkt_recv_total) * 100

    @property
    def buffer_health_percent(self) -> float:
        """Receiver buffer health percentage"""
        # Estimate: if ms_rcv_buf is close to ms_rcv_tsbpd_delay, buffer is healthy
        if self.instantaneous.ms_rcv_tsbpd_delay == 0:
            return 100.0
        ratio = self.instantaneous.ms_rcv_buf / self.instantaneous.ms_rcv_tsbpd_delay
        return min(100.0, ratio * 100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""
        return {
            "timestamp": self.timestamp,
            "connection": {
                "state": self.connection.state.value,
                "up_time_seconds": self.connection.up_time_seconds,
                "up_time_formatted": self._format_duration(self.connection.up_time_seconds),
                "source_address": self.connection.source_address,
                "local_port": self.connection.local_port,
                "peer_latency_ms": self.connection.peer_latency_ms,
                "recv_latency_ms": self.connection.recv_latency_ms,
                "encryption": self.connection.encryption,
                "stream_id": self.connection.stream_id,
                "reconnections": self.connection.reconnections,
                "last_error": self.connection.last_error,
            },
            "network": {
                "rtt_ms": round(self.instantaneous.ms_rtt, 2),
                "bandwidth_mbps": round(self.instantaneous.mbps_bandwidth, 2),
                "max_bw_mbps": round(self.instantaneous.mbps_max_bw, 2),
                "recv_rate_mbps": round(self.interval.mbps_recv_rate, 2),
                "mss_bytes": self.instantaneous.byte_mss,
            },
            "packets": {
                "recv_total": self.accumulated.pkt_recv_total,
                "recv_unique_total": self.accumulated.pkt_recv_unique_total,
                "loss_total": self.accumulated.pkt_rcv_loss_total,
                "retrans_total": self.accumulated.pkt_rcv_retrans_total,
                "drop_total": self.accumulated.pkt_rcv_drop_total,
                "undecrypt_total": self.accumulated.pkt_rcv_undecrypt_total,
                "loss_rate_percent": round(self.packet_loss_rate, 3),
                "drop_rate_percent": round(self.drop_rate, 3),
                "retrans_ratio_percent": round(self.retransmission_ratio, 3),
            },
            "bytes": {
                "recv_total": self.accumulated.byte_recv_total,
                "recv_unique_total": self.accumulated.byte_recv_unique_total,
                "loss_total": self.accumulated.byte_rcv_loss_total,
                "drop_total": self.accumulated.byte_rcv_drop_total,
            },
            "buffer": {
                "avail_bytes": self.instantaneous.byte_avail_rcv_buf,
                "packets": self.instantaneous.pkt_rcv_buf,
                "bytes": self.instantaneous.byte_rcv_buf,
                "timespan_ms": round(self.instantaneous.ms_rcv_buf, 2),
                "tsbpd_delay_ms": self.instantaneous.ms_rcv_tsbpd_delay,
                "health_percent": round(self.buffer_health_percent, 1),
            },
            "interval": {
                "recv_unique": self.interval.pkt_recv_unique,
                "drop": self.interval.pkt_rcv_drop,
                "belated": self.interval.pkt_rcv_belated,
                "reorder_distance": self.interval.pkt_reorder_distance,
                "recv_rate_mbps": round(self.interval.mbps_recv_rate, 2),
            },
            "congestion": {
                "congestion_window": self.instantaneous.pkt_congestion_window,
                "flight_size": self.instantaneous.pkt_flight_size,
                "reorder_tolerance": self.instantaneous.pkt_reorder_tolerance,
                "avg_belated_time_ms": round(self.instantaneous.pkt_rcv_avg_belated_time, 2),
            },
        }

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds as Makito-style duration: 1d22h5m41s"""
        if seconds < 60:
            return f"{int(seconds)}s"
        mins, secs = divmod(int(seconds), 60)
        if mins < 60:
            return f"{mins}m{secs}s"
        hours, mins = divmod(mins, 60)
        if hours < 24:
            return f"{hours}h{mins}m{secs}s"
        days, hours = divmod(hours, 24)
        return f"{days}d{hours}h{mins}m{secs}s"


class SRTStatsCollector:
    """
    Collects and aggregates SRT statistics from raw socket data.
    Mimics Haivision Makito x4 statistics display.
    """

    def __init__(self, stats_interval_ms: int = 1000):
        self.stats_interval_ms = stats_interval_ms
        self._last_update = 0.0
        self._snapshot = SRTMetricsSnapshot()
        self._history: list[SRTMetricsSnapshot] = []
        self._max_history = 3600  # 1 hour at 1/sec

    def update_from_srt_socket(self, raw_stats: Dict[str, Any]) -> SRTMetricsSnapshot:
        """
        Update metrics from SRT socket statistics (srt_bstats/srt_bistats output).

        Args:
            raw_stats: Dict with SRT statistic fields (msRTT, pktRecvTotal, etc.)
        """
        now = time.time()

        # Update accumulated stats
        acc = self._snapshot.accumulated
        acc.ms_time_stamp = raw_stats.get("msTimeStamp", 0)
        acc.pkt_recv_total = raw_stats.get("pktRecvTotal", 0)
        acc.pkt_recv_unique_total = raw_stats.get("pktRecvUniqueTotal", 0)
        acc.pkt_rcv_loss_total = raw_stats.get("pktRcvLossTotal", 0)
        acc.pkt_rcv_retrans_total = raw_stats.get("pktRcvRetransTotal", 0)
        acc.pkt_rcv_drop_total = raw_stats.get("pktRcvDropTotal", 0)
        acc.pkt_rcv_undecrypt_total = raw_stats.get("pktRcvUndecryptTotal", 0)
        acc.pkt_sent_ack_total = raw_stats.get("pktSentACKTotal", 0)
        acc.pkt_sent_nak_total = raw_stats.get("pktSentNAKTotal", 0)

        acc.byte_recv_total = raw_stats.get("byteRecvTotal", 0)
        acc.byte_recv_unique_total = raw_stats.get("byteRecvUniqueTotal", 0)
        acc.byte_rcv_loss_total = raw_stats.get("byteRcvLossTotal", 0)
        acc.byte_rcv_drop_total = raw_stats.get("byteRcvDropTotal", 0)
        acc.byte_rcv_undecrypt_total = raw_stats.get("byteRcvUndecryptTotal", 0)

        # Update interval stats
        interval = self._snapshot.interval
        interval.pkt_recv_unique = raw_stats.get("pktRecvUnique", 0)
        interval.pkt_rcv_drop = raw_stats.get("pktRcvDrop", 0)
        interval.pkt_rcv_undecrypt = raw_stats.get("pktRcvUndecrypt", 0)
        interval.pkt_rcv_belated = raw_stats.get("pktRcvBelated", 0)
        interval.pkt_reorder_distance = raw_stats.get("pktReorderDistance", 0)
        interval.byte_recv_unique = raw_stats.get("byteRecvUnique", 0)
        interval.byte_rcv_drop = raw_stats.get("byteRcvDrop", 0)
        interval.mbps_recv_rate = raw_stats.get("mbpsRecvRate", 0.0)
        interval.us_snd_duration = raw_stats.get("usSndDuration", 0)

        # Update instantaneous stats
        inst = self._snapshot.instantaneous
        inst.ms_rtt = raw_stats.get("msRTT", 0.0)
        inst.mbps_bandwidth = raw_stats.get("mbpsBandwidth", 0.0)
        inst.mbps_max_bw = raw_stats.get("mbpsMaxBW", 0.0)
        inst.byte_avail_rcv_buf = raw_stats.get("byteAvailRcvBuf", 0)
        inst.pkt_rcv_buf = raw_stats.get("pktRcvBuf", 0)
        inst.byte_rcv_buf = raw_stats.get("byteRcvBuf", 0)
        inst.ms_rcv_buf = raw_stats.get("msRcvBuf", 0.0)
        inst.ms_rcv_tsbpd_delay = raw_stats.get("msRcvTsbPdDelay", 0)
        inst.pkt_congestion_window = raw_stats.get("pktCongestionWindow", 0)
        inst.pkt_flight_size = raw_stats.get("pktFlightSize", 0)
        inst.pkt_reorder_tolerance = raw_stats.get("pktReorderTolerance", 0)
        inst.pkt_rcv_avg_belated_time = raw_stats.get("pktRcvAvgBelatedTime", 0.0)
        inst.byte_mss = raw_stats.get("byteMSS", 1500)

        self._snapshot.timestamp = now

        # Store history
        self._history.append(self._snapshot)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        return self._snapshot

    def update_connection_state(self, state: SRTConnectionState, **kwargs) -> None:
        """Update connection metadata"""
        self._snapshot.connection.state = state
        for key, value in kwargs.items():
            if hasattr(self._snapshot.connection, key):
                setattr(self._snapshot.connection, key, value)

    def get_snapshot(self) -> SRTMetricsSnapshot:
        """Get current metrics snapshot"""
        return self._snapshot

    def get_history(self, seconds: int = 60) -> list[SRTMetricsSnapshot]:
        """Get historical snapshots for charting"""
        cutoff = time.time() - seconds
        return [s for s in self._history if s.timestamp >= cutoff]

    def reset(self) -> None:
        """Reset all statistics (like Makito Reset button)"""
        self._snapshot = SRTMetricsSnapshot()
        self._history.clear()
        self._last_update = 0.0
