"""
Core Models - Data Contracts for Media Stream Analyzer
Updated for Sprint 4: SRT Input + Video Analysis

All dataclasses are JSON-serializable via to_dict() methods.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


# ============== Audio Metrics (Sprint 1-3) ==============

class DBFSZone(Enum):
    DANGER = "danger"      # -6..0 dBFS
    WARNING = "warning"    # -9..-6 dBFS
    CAUTION = "caution"    # -18..-9 dBFS
    SAFE = "safe"          # -60..-18 dBFS
    QUIET = "quiet"        # -70..-60 dBFS
    SILENCE = "silence"    # < -70 dBFS


class LUFSZone(Enum):
    DANGER = "danger"      # > -14 LUFS
    TARGET = "target"      # -24..-22 LUFS
    SAFE = "safe"          # -30..-24 LUFS
    QUIET = "quiet"        # -40..-30 LUFS
    SILENCE = "silence"    # < -70 LUFS


@dataclass
class DBFSMetrics:
    """DBFS peak level metrics"""
    left_dbfs: float = -70.0
    right_dbfs: float = -70.0
    peak_dbfs: float = -70.0
    zone: DBFSZone = DBFSZone.SILENCE
    peak_hold_dbfs: float = -70.0
    true_peak_db: float = -70.0
    min_dbfs: float = -70.0
    max_dbfs: float = -70.0
    dynamic_range_db: float = 0.0


@dataclass
class LUFSMetrics:
    """EBU R128 loudness metrics"""
    momentary: float = -70.0    # M - 400ms
    short_term: float = -70.0   # S - 3s
    integrated: float = -70.0   # I - entire program
    zone: LUFSZone = LUFSZone.SILENCE
    peak_hold: float = -70.0
    min_loudness: float = -70.0
    max_loudness: float = -70.0
    lra: float = 0.0            # Loudness Range (LU)


@dataclass
class AudioLevelIndicator:
    """Combined audio level indicator (DBFS + LUFS)"""
    dbfs: DBFSMetrics = field(default_factory=DBFSMetrics)
    lufs: LUFSMetrics = field(default_factory=LUFSMetrics)


@dataclass
class SpectrumMetrics:
    """FFT spectrum metrics"""
    peak_freq_hz: int = 0
    peak_db: float = -70.0
    bands: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class AudioMetrics:
    """Complete audio metrics"""
    level_indicator: AudioLevelIndicator = field(default_factory=AudioLevelIndicator)
    bitrate: Dict[str, float] = field(default_factory=lambda: {
        "instant": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0
    })
    jitter: Dict[str, float] = field(default_factory=lambda: {
        "instant": 0.0, "min": 0.0, "max": 0.0, "avg": 0.0
    })
    spectrum: SpectrumMetrics = field(default_factory=SpectrumMetrics)
    errors: Dict[str, int] = field(default_factory=lambda: {
        "crc_total": 0, "sync_total": 0
    })
    silence_detected: bool = False
    silence_duration_ms: float = 0.0


# ============== Video Metrics (Sprint 4) ==============

@dataclass
class VideoCodecMetrics:
    """Video codec information"""
    codec: str = ""
    profile: str = ""
    level: str = ""
    width: int = 0
    height: int = 0
    fps: float = 0.0
    bit_depth: int = 8
    chroma_subsampling: str = ""
    color_space: str = ""
    scan_type: str = "Progressive"
    bitrate_kbps: int = 0
    bitrate_mode: str = "CBR"


@dataclass
class GOPMetrics:
    """GOP structure metrics"""
    pattern: str = ""           # e.g., "IBBPBBPBBP"
    length: int = 0
    gop_type: str = "open"      # "open" or "closed"
    avg_keyframe_interval_ms: float = 0.0
    last_keyframe_interval_ms: float = 0.0
    scene_changes: int = 0


@dataclass
class FrameDistribution:
    """Frame type distribution"""
    i_frames: int = 0
    p_frames: int = 0
    b_frames: int = 0
    idr_frames: int = 0
    total: int = 0


@dataclass
class VideoMetrics:
    """Complete video metrics"""
    codec: VideoCodecMetrics = field(default_factory=VideoCodecMetrics)
    gop: GOPMetrics = field(default_factory=GOPMetrics)
    frames: FrameDistribution = field(default_factory=FrameDistribution)
    health: Dict[str, Any] = field(default_factory=lambda: {
        "frame_drops": 0,
        "decode_errors": 0,
        "buffer_health_ms": 0.0,
    })


# ============== SRT Metrics (Sprint 4) ==============

@dataclass
class SRTConnectionMetrics:
    """SRT connection state metrics"""
    state: str = "STOPPED"           # STREAMING, CONNECTING, etc.
    up_time_seconds: float = 0.0
    up_time_formatted: str = "0s"
    source_address: str = ""
    local_port: int = 0
    peer_latency_ms: int = 120
    recv_latency_ms: int = 120
    encryption: str = "none"
    stream_id: str = ""
    reconnections: int = 0
    last_error: Optional[str] = None


@dataclass
class SRTNetworkMetrics:
    """SRT network layer metrics"""
    rtt_ms: float = 0.0
    bandwidth_mbps: float = 0.0
    max_bw_mbps: float = 0.0
    recv_rate_mbps: float = 0.0
    mss_bytes: int = 1500


@dataclass
class SRTPacketMetrics:
    """SRT packet statistics"""
    recv_total: int = 0
    recv_unique_total: int = 0
    loss_total: int = 0
    retrans_total: int = 0
    drop_total: int = 0
    undecrypt_total: int = 0
    loss_rate_percent: float = 0.0
    drop_rate_percent: float = 0.0
    retrans_ratio_percent: float = 0.0


@dataclass
class SRTBufferMetrics:
    """SRT buffer metrics"""
    avail_bytes: int = 0
    packets: int = 0
    bytes: int = 0
    timespan_ms: float = 0.0
    tsbpd_delay_ms: int = 0
    health_percent: float = 100.0


@dataclass
class SRTCongestionMetrics:
    """SRT congestion control metrics"""
    congestion_window: int = 0
    flight_size: int = 0
    reorder_tolerance: int = 0
    avg_belated_time_ms: float = 0.0


@dataclass
class SRTMetrics:
    """Complete SRT metrics (Haivision Makito x4 style)"""
    connection: SRTConnectionMetrics = field(default_factory=SRTConnectionMetrics)
    network: SRTNetworkMetrics = field(default_factory=SRTNetworkMetrics)
    packets: SRTPacketMetrics = field(default_factory=SRTPacketMetrics)
    buffer: SRTBufferMetrics = field(default_factory=SRTBufferMetrics)
    congestion: SRTCongestionMetrics = field(default_factory=SRTCongestionMetrics)


# ============== Metadata (Sprint 1) ==============

@dataclass
class ArtisticMetadata:
    """Stream metadata - artistic column"""
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    station: str = ""
    icy_name: str = ""


@dataclass
class TechnicalMetadata:
    """Stream metadata - technical column"""
    codec: str = ""
    profile: str = ""
    sample_rate: int = 0
    channels: int = 0
    bitrate: int = 0
    bitrate_mode: str = "CBR"
    container: str = ""


@dataclass
class StreamMetadata:
    """Combined stream metadata"""
    artistic: ArtisticMetadata = field(default_factory=ArtisticMetadata)
    technical: TechnicalMetadata = field(default_factory=TechnicalMetadata)


# ============== Complete Metrics Snapshot ==============

@dataclass
class MetricsSnapshot:
    """
    Complete metrics snapshot for WebSocket/REST API.
    Sent every second via WebSocket.
    """
    timestamp: float = 0.0
    session_duration: float = 0.0

    # Audio (Sprint 1-3)
    audio: AudioMetrics = field(default_factory=AudioMetrics)

    # Video (Sprint 4)
    video: VideoMetrics = field(default_factory=VideoMetrics)

    # SRT (Sprint 4)
    srt: SRTMetrics = field(default_factory=SRTMetrics)

    # Metadata
    metadata: StreamMetadata = field(default_factory=StreamMetadata)

    # Time window
    time_window: str = "1m"  # 1m, 5m, 15m, 30m, 60m

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "timestamp": self.timestamp,
            "session_duration": self.session_duration,
            "time_window": self.time_window,
            "audio": {
                "level_indicator": {
                    "dbfs_left": round(self.audio.level_indicator.dbfs.left_dbfs, 1),
                    "dbfs_right": round(self.audio.level_indicator.dbfs.right_dbfs, 1),
                    "dbfs_peak": round(self.audio.level_indicator.dbfs.peak_dbfs, 1),
                    "dbfs_zone": self.audio.level_indicator.dbfs.zone.value,
                    "lufs_momentary": round(self.audio.level_indicator.lufs.momentary, 1),
                    "lufs_short_term": round(self.audio.level_indicator.lufs.short_term, 1),
                    "lufs_integrated": round(self.audio.level_indicator.lufs.integrated, 1),
                    "lufs_zone": self.audio.level_indicator.lufs.zone.value,
                    "dbfs_peak_hold": round(self.audio.level_indicator.dbfs.peak_hold_dbfs, 1),
                    "lufs_peak_hold": round(self.audio.level_indicator.lufs.peak_hold, 1),
                    "true_peak_db": round(self.audio.level_indicator.dbfs.true_peak_db, 1),
                    "min_dbfs": round(self.audio.level_indicator.dbfs.min_dbfs, 1),
                    "max_dbfs": round(self.audio.level_indicator.dbfs.max_dbfs, 1),
                    "dynamic_range_db": round(self.audio.level_indicator.dbfs.dynamic_range_db, 1),
                    "lra": round(self.audio.level_indicator.lufs.lra, 1),
                },
                "bitrate": self.audio.bitrate,
                "jitter": self.audio.jitter,
                "spectrum": {
                    "peak_freq": self.audio.spectrum.peak_freq_hz,
                    "peak_db": round(self.audio.spectrum.peak_db, 1),
                },
                "errors": self.audio.errors,
                "silence": {
                    "detected": self.audio.silence_detected,
                    "duration_ms": round(self.audio.silence_duration_ms, 1),
                },
            },
            "video": {
                "codec": {
                    "name": self.video.codec.codec,
                    "profile": self.video.codec.profile,
                    "level": self.video.codec.level,
                    "badge": f"{self.video.codec.codec} {self.video.codec.profile}".strip(),
                },
                "resolution": {
                    "width": self.video.codec.width,
                    "height": self.video.codec.height,
                    "badge": f"{self.video.codec.width}x{self.video.codec.height}" if self.video.codec.width > 0 else "?",
                    "scan_type": self.video.codec.scan_type,
                },
                "frame_rate": {
                    "fps": self.video.codec.fps,
                },
                "color": {
                    "bit_depth": self.video.codec.bit_depth,
                    "chroma_subsampling": self.video.codec.chroma_subsampling,
                    "color_space": self.video.codec.color_space,
                },
                "gop": {
                    "pattern": self.video.gop.pattern,
                    "length": self.video.gop.length,
                    "type": self.video.gop.gop_type,
                    "avg_keyframe_interval_ms": round(self.video.gop.avg_keyframe_interval_ms, 1),
                    "last_keyframe_interval_ms": round(self.video.gop.last_keyframe_interval_ms, 1),
                },
                "frame_distribution": {
                    "i_frames": self.video.frames.i_frames,
                    "p_frames": self.video.frames.p_frames,
                    "b_frames": self.video.frames.b_frames,
                    "idr_frames": self.video.frames.idr_frames,
                    "total": self.video.frames.total,
                },
                "bitrate": {
                    "video_kbps": self.video.codec.bitrate_kbps,
                    "mode": self.video.codec.bitrate_mode,
                },
                "health": self.video.health,
            },
            "srt": {
                "connection": {
                    "state": self.srt.connection.state,
                    "up_time": self.srt.connection.up_time_formatted,
                    "up_time_seconds": round(self.srt.connection.up_time_seconds, 1),
                    "source_address": self.srt.connection.source_address,
                    "local_port": self.srt.connection.local_port,
                    "peer_latency_ms": self.srt.connection.peer_latency_ms,
                    "recv_latency_ms": self.srt.connection.recv_latency_ms,
                    "encryption": self.srt.connection.encryption,
                    "stream_id": self.srt.connection.stream_id,
                    "reconnections": self.srt.connection.reconnections,
                    "last_error": self.srt.connection.last_error,
                },
                "network": {
                    "rtt_ms": round(self.srt.network.rtt_ms, 2),
                    "bandwidth_mbps": round(self.srt.network.bandwidth_mbps, 2),
                    "max_bw_mbps": round(self.srt.network.max_bw_mbps, 2),
                    "recv_rate_mbps": round(self.srt.network.recv_rate_mbps, 2),
                    "mss_bytes": self.srt.network.mss_bytes,
                },
                "packets": {
                    "recv_total": self.srt.packets.recv_total,
                    "recv_unique_total": self.srt.packets.recv_unique_total,
                    "loss_total": self.srt.packets.loss_total,
                    "retrans_total": self.srt.packets.retrans_total,
                    "drop_total": self.srt.packets.drop_total,
                    "undecrypt_total": self.srt.packets.undecrypt_total,
                    "loss_rate_percent": round(self.srt.packets.loss_rate_percent, 3),
                    "drop_rate_percent": round(self.srt.packets.drop_rate_percent, 3),
                    "retrans_ratio_percent": round(self.srt.packets.retrans_ratio_percent, 3),
                },
                "buffer": {
                    "avail_bytes": self.srt.buffer.avail_bytes,
                    "packets": self.srt.buffer.packets,
                    "bytes": self.srt.buffer.bytes,
                    "timespan_ms": round(self.srt.buffer.timespan_ms, 2),
                    "tsbpd_delay_ms": self.srt.buffer.tsbpd_delay_ms,
                    "health_percent": round(self.srt.buffer.health_percent, 1),
                },
                "congestion": {
                    "congestion_window": self.srt.congestion.congestion_window,
                    "flight_size": self.srt.congestion.flight_size,
                    "reorder_tolerance": self.srt.congestion.reorder_tolerance,
                    "avg_belated_time_ms": round(self.srt.congestion.avg_belated_time_ms, 2),
                },
            },
            "metadata": {
                "artistic": {
                    "title": self.metadata.artistic.title,
                    "artist": self.metadata.artistic.artist,
                    "album": self.metadata.artistic.album,
                    "genre": self.metadata.artistic.genre,
                    "station": self.metadata.artistic.station,
                    "icy_name": self.metadata.artistic.icy_name,
                },
                "technical": {
                    "codec": self.metadata.technical.codec,
                    "profile": self.metadata.technical.profile,
                    "sample_rate": self.metadata.technical.sample_rate,
                    "channels": self.metadata.technical.channels,
                    "bitrate": self.metadata.technical.bitrate,
                    "bitrate_mode": self.metadata.technical.bitrate_mode,
                    "container": self.metadata.technical.container,
                },
            },
        }
