"""Video keyframe extractor for real-time stream analysis.

Extracts keyframes (I-frames/IDR) from video stream using FFmpeg
and analyzes GOP structure.
"""
import asyncio
import logging
import subprocess
import numpy as np
from typing import Optional, Callable, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import IntEnum
from collections import deque

logger = logging.getLogger(__name__)


class FrameType(IntEnum):
    """Video frame types."""
    UNKNOWN = 0
    IDR = 1      # Instantaneous Decoder Refresh
    I = 2        # Intra (keyframe, not IDR)
    P = 3        # Predicted
    B = 4        # Bi-directional


@dataclass
class VideoFrame:
    """Video frame information."""
    timestamp: float
    frame_type: FrameType
    frame_number: int
    width: int
    height: int
    is_keyframe: bool
    pts: int
    dts: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "frame_type": self.frame_type.name,
            "frame_number": self.frame_number,
            "width": self.width,
            "height": self.height,
            "is_keyframe": self.is_keyframe,
            "pts": self.pts,
            "dts": self.dts,
        }


@dataclass
class GOPStructure:
    """GOP (Group of Pictures) structure."""
    frames: List[VideoFrame]
    gop_size: int
    idr_interval: int
    has_b_frames: bool

    @property
    def i_count(self) -> int:
        return sum(1 for f in self.frames if f.frame_type in (FrameType.I, FrameType.IDR))

    @property
    def p_count(self) -> int:
        return sum(1 for f in self.frames if f.frame_type == FrameType.P)

    @property
    def b_count(self) -> int:
        return sum(1 for f in self.frames if f.frame_type == FrameType.B)

    @property
    def idr_count(self) -> int:
        return sum(1 for f in self.frames if f.frame_type == FrameType.IDR)

    @property
    def pattern(self) -> str:
        """Return GOP pattern string (e.g., 'IDRBBPBBPBBPBB')."""
        return ''.join(f.frame_type.name for f in self.frames)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gop_size": self.gop_size,
            "idr_interval": self.idr_interval,
            "has_b_frames": self.has_b_frames,
            "i_count": self.i_count,
            "p_count": self.p_count,
            "b_count": self.b_count,
            "idr_count": self.idr_count,
            "pattern": self.pattern,
            "frames": [f.to_dict() for f in self.frames],
        }


@dataclass
class KeyframeImage:
    """Extracted keyframe image data."""
    timestamp: float
    frame_number: int
    width: int
    height: int
    rgb_data: np.ndarray  # (height, width, 3) uint8

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "width": self.width,
            "height": self.height,
        }


class VideoKeyframeExtractor:
    """Extract keyframes and analyze GOP structure from video stream."""

    def __init__(self, ffmpeg_path: str = "ffmpeg", ffprobe_path: str = "ffprobe"):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path

        self._process: Optional[subprocess.Popen] = None
        self._running = False

        # Callbacks
        self._keyframe_callbacks: List[Callable[[KeyframeImage], None]] = []
        self._gop_callbacks: List[Callable[[GOPStructure], None]] = []
        self._frame_callbacks: List[Callable[[VideoFrame], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        # GOP tracking
        self._current_gop: List[VideoFrame] = []
        self._frame_count: int = 0
        self._last_idr_frame: int = 0

        # Keyframe buffer
        self._keyframe_buffer: deque = deque(maxlen=10)

        logger.info("VideoKeyframeExtractor initialized")

    def on_keyframe(self, callback: Callable[[KeyframeImage], None]):
        """Register keyframe image callback."""
        self._keyframe_callbacks.append(callback)

    def on_gop(self, callback: Callable[[GOPStructure], None]):
        """Register GOP structure callback."""
        self._gop_callbacks.append(callback)

    def on_frame(self, callback: Callable[[VideoFrame], None]):
        """Register frame info callback."""
        self._frame_callbacks.append(callback)

    def on_error(self, callback: Callable[[str], None]):
        """Register error callback."""
        self._error_callbacks.append(callback)

    def _notify_keyframe(self, image: KeyframeImage):
        for cb in self._keyframe_callbacks:
            try:
                cb(image)
            except Exception as e:
                logger.error(f"Keyframe callback error: {e}")

    def _notify_gop(self, gop: GOPStructure):
        for cb in self._gop_callbacks:
            try:
                cb(gop)
            except Exception as e:
                logger.error(f"GOP callback error: {e}")

    def _notify_frame(self, frame: VideoFrame):
        for cb in self._frame_callbacks:
            try:
                cb(frame)
            except Exception as e:
                logger.error(f"Frame callback error: {e}")

    def _notify_error(self, message: str):
        logger.error(message)
        for cb in self._error_callbacks:
            try:
                cb(message)
            except Exception:
                pass

    def start(self, input_url: str) -> bool:
        """Start keyframe extraction from video stream.

        Uses FFmpeg to extract keyframes as raw RGB images.
        """
        try:
            # Command to extract keyframes only
            cmd = [
                self.ffmpeg_path,
                "-i", input_url,
                "-vf", "select=eq(pict_type\,I),scale=320:-1",  # Select I-frames, scale to 320px width
                "-vsync", "vfr",  # Variable frame rate (only keyframes)
                "-f", "rawvideo",
                "-pix_fmt", "rgb24",
                "pipe:1"
            ]

            # Command to get frame info
            info_cmd = [
                self.ffmpeg_path,
                "-i", input_url,
                "-vf", "select=eq(pict_type\,I),showinfo",
                "-f", "null",
                "-"
            ]

            logger.info(f"Starting keyframe extraction: {input_url}")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
            )

            self._running = True

            # Start reading threads
            import threading
            self._stdout_thread = threading.Thread(
                target=self._read_keyframes,
                args=(320, 180),  # Approximate dimensions
                daemon=True
            )
            self._stderr_thread = threading.Thread(
                target=self._read_frame_info,
                daemon=True
            )

            self._stdout_thread.start()
            self._stderr_thread.start()

            logger.info("Keyframe extraction started")
            return True

        except FileNotFoundError:
            self._notify_error(f"FFmpeg not found: {self.ffmpeg_path}")
            return False
        except Exception as e:
            self._notify_error(f"Failed to start keyframe extraction: {e}")
            return False

    def _read_keyframes(self, width: int, height: int):
        """Read keyframe images from FFmpeg stdout."""
        if not self._process or not self._process.stdout:
            return

        frame_size = width * height * 3  # RGB24

        try:
            while self._running:
                raw_data = self._process.stdout.read(frame_size)

                if not raw_data:
                    if self._process.poll() is not None:
                        break
                    continue

                if len(raw_data) < frame_size:
                    continue

                # Convert to numpy array
                image_data = np.frombuffer(raw_data[:frame_size], dtype=np.uint8)
                image_data = image_data.reshape(height, width, 3)

                keyframe = KeyframeImage(
                    timestamp=0,  # Will be updated from PTS info
                    frame_number=self._frame_count,
                    width=width,
                    height=height,
                    rgb_data=image_data
                )

                self._keyframe_buffer.append(keyframe)
                self._notify_keyframe(keyframe)

        except Exception as e:
            self._notify_error(f"Keyframe read error: {e}")

    def _read_frame_info(self):
        """Read frame information from FFmpeg stderr."""
        if not self._process or not self._process.stderr:
            return

        try:
            for line in iter(self._process.stderr.readline, b""):
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()

                # Parse frame info from showinfo filter
                # Example: "n: 0 pts: 0 pts_time:0 t:0.000000 ... type:I"
                if "type:I" in line_str or "type:IDR" in line_str:
                    self._frame_count += 1

                    # Extract PTS if available
                    pts = 0
                    if "pts:" in line_str:
                        try:
                            pts_str = line_str.split("pts:")[1].split()[0]
                            pts = int(pts_str)
                        except (IndexError, ValueError):
                            pass

                    frame_type = FrameType.IDR if "IDR" in line_str else FrameType.I

                    frame = VideoFrame(
                        timestamp=pts / 90000.0 if pts else 0,  # 90kHz clock
                        frame_type=frame_type,
                        frame_number=self._frame_count,
                        width=0,
                        height=0,
                        is_keyframe=True,
                        pts=pts,
                        dts=pts,
                    )

                    self._notify_frame(frame)
                    self._handle_gop_frame(frame)

        except Exception as e:
            logger.error(f"Frame info read error: {e}")

    def _handle_gop_frame(self, frame: VideoFrame):
        """Handle frame for GOP structure analysis."""
        if frame.frame_type == FrameType.IDR:
            # New GOP starts with IDR
            if self._current_gop:
                # Finalize previous GOP
                gop = GOPStructure(
                    frames=self._current_gop.copy(),
                    gop_size=len(self._current_gop),
                    idr_interval=frame.frame_number - self._last_idr_frame,
                    has_b_frames=any(f.frame_type == FrameType.B for f in self._current_gop)
                )
                self._notify_gop(gop)

            self._current_gop = [frame]
            self._last_idr_frame = frame.frame_number
        else:
            self._current_gop.append(frame)

    def get_latest_keyframe(self) -> Optional[KeyframeImage]:
        """Get the most recent keyframe."""
        if self._keyframe_buffer:
            return self._keyframe_buffer[-1]
        return None

    def stop(self):
        """Stop keyframe extraction."""
        logger.info("Stopping keyframe extraction...")
        self._running = False

        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            except Exception as e:
                logger.error(f"Error stopping: {e}")

        logger.info("Keyframe extraction stopped")

    async def start_async(self, input_url: str) -> bool:
        """Async version of start."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.start, input_url)

    async def stop_async(self):
        """Async version of stop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.stop)
