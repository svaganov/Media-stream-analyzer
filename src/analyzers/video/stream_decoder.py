"""FFmpeg-based stream decoder for audio/video analysis."""
import asyncio
import logging
import subprocess
import threading
import numpy as np
from typing import Optional, Callable, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class StreamInfo:
    """Stream information extracted from ffprobe."""
    url: str
    protocol: str

    # Video
    has_video: bool = False
    video_codec: str = ""
    video_profile: str = ""
    width: int = 0
    height: int = 0
    frame_rate: float = 0.0
    bit_depth: int = 8
    chroma_subsampling: str = ""
    color_space: str = ""
    scan_type: str = "progressive"
    video_bitrate: int = 0
    gop_size: int = 0

    # Audio
    has_audio: bool = False
    audio_codec: str = ""
    audio_sample_rate: int = 48000
    audio_channels: int = 2
    audio_bitrate: int = 0
    audio_format: str = ""

    # Container
    container_format: str = ""
    duration: float = 0.0
    bitrate: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "protocol": self.protocol,
            "video": {
                "has_video": self.has_video,
                "codec": self.video_codec,
                "profile": self.video_profile,
                "resolution": f"{self.width}x{self.height}" if self.width else "",
                "frame_rate": round(self.frame_rate, 2),
                "bit_depth": self.bit_depth,
                "chroma": self.chroma_subsampling,
                "color_space": self.color_space,
                "scan_type": self.scan_type,
                "bitrate": self.video_bitrate,
                "gop_size": self.gop_size,
            },
            "audio": {
                "has_audio": self.has_audio,
                "codec": self.audio_codec,
                "sample_rate": self.audio_sample_rate,
                "channels": self.audio_channels,
                "bitrate": self.audio_bitrate,
                "format": self.audio_format,
            },
            "container": {
                "format": self.container_format,
                "duration": round(self.duration, 2),
                "bitrate": self.bitrate,
            }
        }


@dataclass
class AudioFrame:
    """Audio frame data."""
    timestamp: float
    samples: np.ndarray  # shape: (channels, samples)
    sample_rate: int
    channels: int

    @property
    def duration(self) -> float:
        return len(self.samples[0]) / self.sample_rate


@dataclass
class VideoFrame:
    """Video frame data."""
    timestamp: float
    data: np.ndarray  # shape: (height, width, 3) RGB
    width: int
    height: int
    is_keyframe: bool = False
    frame_type: str = "P"  # I, P, B, IDR


class StreamDecoder:
    """FFmpeg-based stream decoder."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

        self._process: Optional[subprocess.Popen] = None
        self._running = False

        # Callbacks
        self._audio_callbacks: list[Callable[[AudioFrame], None]] = []
        self._video_callbacks: list[Callable[[VideoFrame], None]] = []
        self._info_callbacks: list[Callable[[StreamInfo], None]] = []

        logger.info(f"StreamDecoder initialized: ffmpeg={ffmpeg_path}")

    def on_audio(self, callback: Callable[[AudioFrame], None]):
        """Register audio frame callback."""
        self._audio_callbacks.append(callback)

    def on_video(self, callback: Callable[[VideoFrame], None]):
        """Register video frame callback."""
        self._video_callbacks.append(callback)

    def on_info(self, callback: Callable[[StreamInfo], None]):
        """Register stream info callback."""
        self._info_callbacks.append(callback)

    async def probe(self, url: str) -> Optional[StreamInfo]:
        """Probe stream to get information."""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                url
            ]

            logger.info(f"Probing stream: {url}")

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"ffprobe failed: {stderr.decode()}")
                return None

            import json
            data = json.loads(stdout.decode())

            info = StreamInfo(url=url, protocol=url.split("://")[0])

            # Parse format info
            if "format" in data:
                fmt = data["format"]
                info.container_format = fmt.get("format_name", "")
                info.duration = float(fmt.get("duration", 0))
                info.bitrate = int(fmt.get("bit_rate", 0))

            # Parse stream info
            if "streams" in data:
                for stream in data["streams"]:
                    codec_type = stream.get("codec_type", "")

                    if codec_type == "video":
                        info.has_video = True
                        info.video_codec = stream.get("codec_name", "")
                        info.video_profile = stream.get("profile", "")
                        info.width = stream.get("width", 0)
                        info.height = stream.get("height", 0)

                        # Frame rate
                        fps_str = stream.get("r_frame_rate", "0/1")
                        try:
                            num, den = fps_str.split("/")
                            info.frame_rate = float(num) / float(den)
                        except:
                            info.frame_rate = 0

                        info.bit_depth = stream.get("bits_per_raw_sample", 8)
                        info.chroma_subsampling = stream.get("pix_fmt", "")
                        info.color_space = stream.get("color_space", "")
                        info.video_bitrate = int(stream.get("bit_rate", 0))

                    elif codec_type == "audio":
                        info.has_audio = True
                        info.audio_codec = stream.get("codec_name", "")
                        info.audio_sample_rate = stream.get("sample_rate", 48000)
                        info.audio_channels = stream.get("channels", 2)
                        info.audio_bitrate = int(stream.get("bit_rate", 0))
                        info.audio_format = stream.get("sample_fmt", "")

            logger.info(f"Stream info: {info.video_codec} {info.width}x{info.height} @ {info.frame_rate}fps")

            for callback in self._info_callbacks:
                callback(info)

            return info

        except Exception as e:
            logger.error(f"Probe error: {e}")
            return None

    async def start(self, url: str, extract_audio: bool = True, 
                    extract_video: bool = True) -> bool:
        """Start decoding stream."""
        try:
            # Build FFmpeg command
            cmd = [self.ffmpeg_path, "-i", url, "-y"]

            # Audio output: raw float32 stereo
            if extract_audio:
                cmd.extend([
                    "-vn",  # no video
                    "-acodec", "pcm_f32le",
                    "-ar", "48000",
                    "-ac", "2",
                    "-f", "f32le",
                    "pipe:1"
                ])

            # Video output: raw RGB frames (if needed)
            if extract_video:
                # For keyframe extraction, we'll use a separate approach
                pass

            logger.info(f"Starting FFmpeg: {' '.join(cmd)}")

            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            self._running = True

            # Start reading audio data
            if extract_audio:
                asyncio.create_task(self._read_audio())

            return True

        except Exception as e:
            logger.error(f"Failed to start decoder: {e}")
            return False

    async def _read_audio(self):
        """Read audio data from FFmpeg output."""
        if not self._process or not self._process.stdout:
            return

        sample_rate = 48000
        channels = 2
        bytes_per_sample = 4  # float32
        frame_size = 1024  # samples per frame
        bytes_per_frame = frame_size * channels * bytes_per_sample

        start_time = asyncio.get_event_loop().time()

        try:
            while self._running:
                raw_data = await self._process.stdout.read(bytes_per_frame)

                if not raw_data or len(raw_data) < bytes_per_frame:
                    break

                # Convert to numpy array
                samples = np.frombuffer(raw_data, dtype=np.float32)
                samples = samples.reshape(-1, channels).T  # (channels, samples)

                frame = AudioFrame(
                    timestamp=asyncio.get_event_loop().time() - start_time,
                    samples=samples,
                    sample_rate=sample_rate,
                    channels=channels
                )

                for callback in self._audio_callbacks:
                    callback(frame)

        except Exception as e:
            logger.error(f"Audio read error: {e}")

    async def extract_keyframe(self, url: str) -> Optional[VideoFrame]:
        """Extract a keyframe from the stream."""
        try:
            cmd = [
                self.ffmpeg_path,
                "-i", url,
                "-ss", "0",
                "-vframes", "1",
                "-f", "rawvideo",
                "-pix_fmt", "rgb24",
                "pipe:1"
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"Keyframe extraction failed: {stderr.decode()}")
                return None

            # Parse dimensions from stderr
            width, height = 1920, 1080  # Default, should parse from stderr

            data = np.frombuffer(stdout, dtype=np.uint8)
            expected_size = width * height * 3

            if len(data) >= expected_size:
                frame_data = data[:expected_size].reshape(height, width, 3)
                return VideoFrame(
                    timestamp=0,
                    data=frame_data,
                    width=width,
                    height=height,
                    is_keyframe=True,
                    frame_type="IDR"
                )

            return None

        except Exception as e:
            logger.error(f"Keyframe extraction error: {e}")
            return None

    async def stop(self):
        """Stop decoding."""
        self._running = False

        if self._process:
            try:
                self._process.terminate()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            except Exception as e:
                logger.error(f"Error stopping decoder: {e}")

        logger.info("Stream decoder stopped")
