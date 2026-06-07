"""Stream metadata parser for FFmpeg output.

Parses codec, resolution, bitrate, and other stream information
from FFmpeg stderr output.
"""
import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VideoStreamInfo:
    """Video stream information."""
    codec: str = ""
    profile: str = ""
    width: int = 0
    height: int = 0
    frame_rate: float = 0.0
    bit_depth: int = 8
    chroma_subsampling: str = ""
    color_space: str = ""
    color_range: str = ""
    bitrate: int = 0
    gop_size: int = 0
    has_b_frames: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "codec": self.codec,
            "profile": self.profile,
            "width": self.width,
            "height": self.height,
            "frame_rate": self.frame_rate,
            "bit_depth": self.bit_depth,
            "chroma_subsampling": self.chroma_subsampling,
            "color_space": self.color_space,
            "color_range": self.color_range,
            "bitrate": self.bitrate,
            "gop_size": self.gop_size,
            "has_b_frames": self.has_b_frames,
        }


@dataclass
class AudioStreamInfo:
    """Audio stream information."""
    codec: str = ""
    sample_rate: int = 48000
    channels: int = 2
    channel_layout: str = ""
    bitrate: int = 0
    sample_format: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "codec": self.codec,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "channel_layout": self.channel_layout,
            "bitrate": self.bitrate,
            "sample_format": self.sample_format,
        }


@dataclass
class ContainerInfo:
    """Container/format information."""
    format: str = ""
    duration: float = 0.0
    bitrate: int = 0
    start_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": self.format,
            "duration": self.duration,
            "bitrate": self.bitrate,
            "start_time": self.start_time,
        }


class StreamMetadataParser:
    """Parse stream metadata from FFmpeg stderr output."""

    # Regex patterns for parsing FFmpeg output
    PATTERNS = {
        # Stream info
        "stream": re.compile(
            r"Stream\s+#\d+:(\d+)(?:\(\w+\))?:\s+"
            r"(\w+):\s+"  # codec type (Video/Audio)
            r"(.+?)"  # codec info
            r"(?:,\s+(.+?))?"  # additional info
            r"$"
        ),

        # Video codec
        "video_codec": re.compile(
            r"(\w+)\s+"  # codec name
            r"\(([^)]+)\)"  # profile/level
        ),

        # Resolution
        "resolution": re.compile(r"(\d+)x(\d+)"),

        # Frame rate
        "fps": re.compile(r"(\d+(?:\.\d+)?)\s*fps"),

        # Bitrate
        "bitrate": re.compile(r"(\d+(?:\.\d+)?)\s*(kb/s|mb/s)"),

        # Duration
        "duration": re.compile(r"Duration:\s+(\d+):(\d+):(\d+\.\d+)"),

        # Format
        "format": re.compile(r"Input\s+#\d+.*from\s+'([^']+)'"),

        # Color info
        "color_space": re.compile(r"(\w+)\s*\((\w+)\s*/\s*(\w+)\s*/\s*(\w+)\)"),
        "color_range": re.compile(r"(tv|pc|mpeg|jpeg)"),

        # Chroma subsampling
        "chroma": re.compile(r"(yuv\d+p?\d*)"),

        # Audio sample rate
        "sample_rate": re.compile(r"(\d+)\s*Hz"),

        # Audio channels
        "channels": re.compile(r"(mono|stereo|(\d\.\d)|(\d+)\s*channels)"),

        # GOP size
        "gop": re.compile(r"gop_size\s*=\s*(\d+)"),

        # B-frames
        "b_frames": re.compile(r"has_b_frames\s*=\s*(\d+)"),
    }

    def __init__(self):
        self.video_info = VideoStreamInfo()
        self.audio_info = AudioStreamInfo()
        self.container_info = ContainerInfo()
        self._raw_lines: List[str] = []

        logger.info("StreamMetadataParser initialized")

    def parse_line(self, line: str) -> bool:
        """Parse a single line of FFmpeg output.

        Returns True if line was successfully parsed.
        """
        line = line.strip()
        if not line:
            return False

        self._raw_lines.append(line)

        # Parse stream info
        if "Stream #" in line:
            return self._parse_stream_line(line)

        # Parse duration
        if "Duration:" in line:
            return self._parse_duration(line)

        # Parse format
        if line.startswith("Input #"):
            return self._parse_format(line)

        # Parse additional video info
        if self.video_info.codec and any(x in line for x in ["yuv", "rgb", "p", "tv", "pc"]):
            return self._parse_video_details(line)

        return False

    def _parse_stream_line(self, line: str) -> bool:
        """Parse stream information line."""
        # Example: Stream #0:0: Video: h264 (High 4.2), yuv420p(tv, bt709, progressive), 1920x1080 [SAR 1:1 DAR 16:9], 5000 kb/s, 25 fps, 25 tbr, 90k tbn, 50 tbc

        try:
            if "Video:" in line:
                return self._parse_video_stream(line)
            elif "Audio:" in line:
                return self._parse_audio_stream(line)
        except Exception as e:
            logger.warning(f"Failed to parse stream line: {e}")

        return False

    def _parse_video_stream(self, line: str) -> bool:
        """Parse video stream information."""
        # Extract codec
        codec_match = re.search(r"Video:\s+(\w+)", line)
        if codec_match:
            self.video_info.codec = codec_match.group(1)

        # Extract profile
        profile_match = re.search(r"\(([^)]+)\)", line)
        if profile_match:
            profile_str = profile_match.group(1)
            # Extract profile and level
            parts = profile_str.split(",")
            if parts:
                self.video_info.profile = parts[0].strip()

        # Extract resolution
        res_match = self.PATTERNS["resolution"].search(line)
        if res_match:
            self.video_info.width = int(res_match.group(1))
            self.video_info.height = int(res_match.group(2))

        # Extract frame rate
        fps_match = self.PATTERNS["fps"].search(line)
        if fps_match:
            self.video_info.frame_rate = float(fps_match.group(1))

        # Extract bitrate
        bitrate_match = self.PATTERNS["bitrate"].search(line)
        if bitrate_match:
            value = float(bitrate_match.group(1))
            unit = bitrate_match.group(2)
            if unit == "mb/s":
                self.video_info.bitrate = int(value * 1000000)
            else:
                self.video_info.bitrate = int(value * 1000)

        # Extract color info
        color_match = self.PATTERNS["color_space"].search(line)
        if color_match:
            self.video_info.color_space = color_match.group(1)

        # Extract chroma subsampling
        chroma_match = self.PATTERNS["chroma"].search(line)
        if chroma_match:
            self.video_info.chroma_subsampling = chroma_match.group(1)

        # Extract bit depth
        if "p10" in line or "10-bit" in line:
            self.video_info.bit_depth = 10
        elif "p12" in line or "12-bit" in line:
            self.video_info.bit_depth = 12

        # Extract GOP size
        gop_match = self.PATTERNS["gop"].search(line)
        if gop_match:
            self.video_info.gop_size = int(gop_match.group(1))

        # Check for B-frames
        b_frames_match = self.PATTERNS["b_frames"].search(line)
        if b_frames_match:
            self.video_info.has_b_frames = int(b_frames_match.group(1)) > 0

        logger.info(f"Parsed video: {self.video_info.codec} {self.video_info.width}x{self.video_info.height} @ {self.video_info.frame_rate}fps")
        return True

    def _parse_audio_stream(self, line: str) -> bool:
        """Parse audio stream information."""
        # Extract codec
        codec_match = re.search(r"Audio:\s+(\w+)", line)
        if codec_match:
            self.audio_info.codec = codec_match.group(1)

        # Extract sample rate
        sr_match = self.PATTERNS["sample_rate"].search(line)
        if sr_match:
            self.audio_info.sample_rate = int(sr_match.group(1))

        # Extract channels
        ch_match = self.PATTERNS["channels"].search(line)
        if ch_match:
            ch_str = ch_match.group(1)
            if ch_str == "mono":
                self.audio_info.channels = 1
                self.audio_info.channel_layout = "mono"
            elif ch_str == "stereo":
                self.audio_info.channels = 2
                self.audio_info.channel_layout = "stereo"
            elif "." in ch_str:
                # Surround format like "5.1"
                self.audio_info.channel_layout = ch_str
                self.audio_info.channels = int(float(ch_str) + 0.5)

        # Extract bitrate
        bitrate_match = self.PATTERNS["bitrate"].search(line)
        if bitrate_match:
            value = float(bitrate_match.group(1))
            unit = bitrate_match.group(2)
            if unit == "mb/s":
                self.audio_info.bitrate = int(value * 1000000)
            else:
                self.audio_info.bitrate = int(value * 1000)

        # Extract sample format
        if "fltp" in line:
            self.audio_info.sample_format = "fltp"
        elif "s16" in line:
            self.audio_info.sample_format = "s16"
        elif "s32" in line:
            self.audio_info.sample_format = "s32"
        elif "f32" in line:
            self.audio_info.sample_format = "f32"

        logger.info(f"Parsed audio: {self.audio_info.codec} {self.audio_info.sample_rate}Hz {self.audio_info.channels}ch")
        return True

    def _parse_duration(self, line: str) -> bool:
        """Parse duration information."""
        match = self.PATTERNS["duration"].search(line)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            self.container_info.duration = hours * 3600 + minutes * 60 + seconds
            return True
        return False

    def _parse_format(self, line: str) -> bool:
        """Parse input format information."""
        # Try to extract format from input line
        if "srt" in line.lower():
            self.container_info.format = "SRT"
        elif "rtmp" in line.lower():
            self.container_info.format = "RTMP"
        elif "udp" in line.lower():
            self.container_info.format = "UDP/MPEG-TS"
        elif "tcp" in line.lower():
            self.container_info.format = "TCP/MPEG-TS"
        else:
            self.container_info.format = "Unknown"
        return True

    def _parse_video_details(self, line: str) -> bool:
        """Parse additional video details."""
        # Color range
        if "tv" in line.lower() or "mpeg" in line.lower():
            self.video_info.color_range = "tv"
        elif "pc" in line.lower() or "jpeg" in line.lower():
            self.video_info.color_range = "pc"

        return True

    def get_stream_info(self) -> Dict[str, Any]:
        """Get complete stream information."""
        return {
            "video": self.video_info.to_dict(),
            "audio": self.audio_info.to_dict(),
            "container": self.container_info.to_dict(),
        }

    def reset(self):
        """Reset all parsed information."""
        self.video_info = VideoStreamInfo()
        self.audio_info = AudioStreamInfo()
        self.container_info = ContainerInfo()
        self._raw_lines.clear()
        logger.info("StreamMetadataParser reset")
