"""Backend configuration for Media Stream Analyzer."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SRTConfig:
    """SRT connection configuration."""
    host: str = "127.0.0.1"
    port: int = 9000
    mode: str = "caller"  # caller, listener, rendezvous
    latency: int = 120  # ms
    passphrase: Optional[str] = None
    pbkeylen: int = 16  # AES-128

    @property
    def url(self) -> str:
        return f"srt://{self.host}:{self.port}"


@dataclass
class WebSocketConfig:
    """WebSocket server configuration."""
    host: str = "0.0.0.0"
    port: int = 8765
    ping_interval: float = 20.0
    ping_timeout: float = 10.0


@dataclass
class FFmpegConfig:
    """FFmpeg configuration."""
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"

    # Audio analysis settings
    audio_sample_rate: int = 48000
    audio_channels: int = 2
    audio_format: str = "f32le"

    # Video analysis settings
    video_format: str = "rawvideo"
    video_pix_fmt: str = "rgb24"


@dataclass
class AnalyzerConfig:
    """Audio analyzer configuration."""
    # DBFS settings
    dbfs_ref_level: float = 0.0  # 0 dBFS = digital full scale
    dbfs_min: float = -70.0
    dbfs_update_interval: float = 0.02  # 50 fps

    # LUFS settings (EBU R128)
    lufs_target: float = -23.0
    lufs_window_m: float = 0.4  # 400ms momentary
    lufs_window_s: float = 3.0  # 3s short-term
    lufs_integration_time: Optional[float] = None  # Infinite for integrated

    # Loudness history
    loudness_history_window: int = 60  # seconds
    loudness_history_interval: float = 1.0  # 1 second update

    # True peak
    true_peak_oversample: int = 4  # 4x oversampling

    # Dynamic range
    lra_percentile_low: float = 10.0  # 10th percentile
    lra_percentile_high: float = 95.0  # 95th percentile


@dataclass
class AppConfig:
    """Application configuration."""
    srt: SRTConfig = None
    websocket: WebSocketConfig = None
    ffmpeg: FFmpegConfig = None
    analyzer: AnalyzerConfig = None
    debug: bool = False
    log_level: str = "INFO"

    def __post_init__(self):
        if self.srt is None:
            self.srt = SRTConfig()
        if self.websocket is None:
            self.websocket = WebSocketConfig()
        if self.ffmpeg is None:
            self.ffmpeg = FFmpegConfig()
        if self.analyzer is None:
            self.analyzer = AnalyzerConfig()


# Default configuration instance
config = AppConfig()
