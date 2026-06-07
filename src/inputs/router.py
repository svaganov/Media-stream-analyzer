"""Input Router - routes streams to appropriate input"""
from typing import Optional
from .factory import InputFactory

class InputRouter:
    """Routes input URLs to appropriate input plugins"""

    @staticmethod
    def detect_input_type(url: str) -> Optional[str]:
        """Detect input type from URL"""
        if url.startswith("srt://"):
            return "srt"
        elif url.startswith("http://") or url.startswith("https://"):
            return "icecast"
        elif url.startswith("ndi://"):
            return "ndi"
        elif url.startswith("sdi://"):
            return "sdi"
        elif url.startswith("rtmp://"):
            return "rtmp"
        elif url.startswith("rtsp://"):
            return "rtsp"
        elif url.startswith("udp://") or url.startswith("rtp://"):
            return "mpegts"
        return None

    @staticmethod
    def create_input(url: str, **kwargs):
        """Create appropriate input for URL"""
        input_type = InputRouter.detect_input_type(url)
        if not input_type:
            raise ValueError(f"Cannot detect input type for: {url}")
        return InputFactory.create(input_type, **kwargs)
