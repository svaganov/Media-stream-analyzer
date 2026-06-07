"""Global configuration"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AppConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"
    default_time_window: str = "1m"

    # SRT defaults
    srt_default_latency: int = 120
    srt_default_mss: int = 1500

    # Test URLs
    test_icecast_url: str = "https://solovievfm.hostingradio.ru/solovievfm256.mp3"

    @classmethod
    def from_env(cls):
        return cls(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8000)),
            log_level=os.getenv("LOG_LEVEL", "info"),
            default_time_window=os.getenv("DEFAULT_TIME_WINDOW", "1m"),
            srt_default_latency=int(os.getenv("SRT_DEFAULT_LATENCY", 120)),
        )

config = AppConfig.from_env()
