"""
SRT Input Plugin for Media Stream Analyzer

Integrates SRT connection manager with the project's input plugin architecture.
Receives SRT stream, demuxes via FFmpeg, and provides frames to analyzers.

Usage:
    input = SRTInput(SRTConnectionConfig(mode=SRTMode.CALLER, host="192.168.1.100", port=9000))
    await input.start()
    frame = await input.get_frame()
    await input.stop()
"""

import asyncio
import logging
import subprocess
import threading
import queue
from typing import Optional, AsyncIterator, Dict, Any
from pathlib import Path

from ..base import BaseInput
from .srt_connection import SRTConnectionManager, SRTConnectionConfig, SRTMode
from .srt_statistics import SRTMetricsSnapshot

logger = logging.getLogger(__name__)


class SRTInput(BaseInput):
    """
    SRT Input Plugin

    Receives SRT stream and outputs raw TS packets or demuxed frames.
    Supports Caller, Listener, and Rendezvous modes.
    """

    INPUT_TYPE = "srt"
    SUPPORTED_CODECS = ["h264", "hevc", "mpeg2video", "aac", "mp3", "ac3", "eac3"]

    def __init__(self, config: Optional[SRTConnectionConfig] = None):
        super().__init__()
        self.config = config or SRTConnectionConfig()
        self.connection = SRTConnectionManager(self.config)

        # Frame queue for analyzer consumption
        self._frame_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._metadata_queue: asyncio.Queue = asyncio.Queue(maxsize=10)

        # FFmpeg process for demuxing
        self._ffmpeg_process: Optional[subprocess.Popen] = None
        self._ffmpeg_task: Optional[asyncio.Task] = None

        # Stream info
        self._stream_info: Dict[str, Any] = {}
        self._running = False

    async def start(self) -> None:
        """Start SRT input: connect + start FFmpeg demux"""
        await super().start()
        self._running = True

        # Start SRT connection
        await self.connection.start()

        # Wait for connection
        timeout = 30.0
        start_time = asyncio.get_event_loop().time()
        while not self.connection.is_connected:
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError("SRT connection timeout")
            await asyncio.sleep(0.1)

        # Start FFmpeg demuxing
        self._ffmpeg_task = asyncio.create_task(self._ffmpeg_loop())

        logger.info(f"SRT input started: {self.config.mode.value} {self.config.host}:{self.config.port}")

    async def _ffmpeg_loop(self) -> None:
        """FFmpeg demuxing loop"""
        srt_url = self.connection._build_srt_url()

        # FFmpeg command: receive SRT, output rawvideo + s16le audio to pipe
        # For production, use more sophisticated pipeline
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel", "error",
            "-i", srt_url,
            "-map", "0:v:0",
            "-c:v", "rawvideo",
            "-pix_fmt", "yuv420p",
            "-f", "rawvideo",
            "pipe:1",
            "-map", "0:a:0?",
            "-c:a", "pcm_s16le",
            "-ar", "48000",
            "-ac", "2",
            "-f", "s16le",
            "pipe:3",
        ]

        try:
            # Start FFmpeg with multiple pipes
            self._ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,      # Video pipe
                stderr=subprocess.PIPE,      # Error output
                pass_fds=(3,),               # Audio pipe (fd 3)
                bufsize=1024*1024,
            )

            # Read video frames
            while self._running and self._ffmpeg_process.poll() is None:
                # Read frame data (simplified - production would parse properly)
                frame_data = await self._read_frame()
                if frame_data:
                    try:
                        self._frame_queue.put_nowait(frame_data)
                    except asyncio.QueueFull:
                        # Drop oldest frame
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait(frame_data)
                        except asyncio.QueueEmpty:
                            pass

                await asyncio.sleep(0.001)  # 1ms to prevent CPU spin

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"FFmpeg loop error: {e}")
        finally:
            if self._ffmpeg_process:
                self._ffmpeg_process.terminate()
                try:
                    self._ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._ffmpeg_process.kill()

    async def _read_frame(self) -> Optional[Dict[str, Any]]:
        """Read a frame from FFmpeg output"""
        # Simplified - production would parse rawvideo properly
        # For now, return metadata about stream
        if not self._ffmpeg_process or self._ffmpeg_process.poll() is not None:
            return None

        # Read from stderr for stream info
        import select
        if select.select([self._ffmpeg_process.stderr], [], [], 0)[0]:
            line = self._ffmpeg_process.stderr.readline()
            if line:
                self._parse_ffmpeg_output(line.decode('utf-8', errors='ignore'))

        return {
            "type": "srt_frame",
            "timestamp": asyncio.get_event_loop().time(),
            "source": "srt",
        }

    def _parse_ffmpeg_output(self, line: str) -> None:
        """Parse FFmpeg stderr for stream information"""
        # Parse codec info, bitrate, etc. from FFmpeg output
        if "Stream #" in line and "Video:" in line:
            # Extract video codec info
            parts = line.split("Video:")[1].split(",")
            self._stream_info["video_codec"] = parts[0].strip().split(" ")[0]
        elif "Stream #" in line and "Audio:" in line:
            parts = line.split("Audio:")[1].split(",")
            self._stream_info["audio_codec"] = parts[0].strip().split(" ")[0]

    async def get_frame(self) -> Optional[Dict[str, Any]]:
        """Get next frame from queue (non-blocking)"""
        try:
            return self._frame_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def get_frames(self) -> AsyncIterator[Dict[str, Any]]:
        """Async iterator for frames"""
        while self._running:
            frame = await self.get_frame()
            if frame:
                yield frame
            else:
                await asyncio.sleep(0.001)

    async def stop(self) -> None:
        """Stop SRT input"""
        self._running = False

        if self._ffmpeg_task:
            self._ffmpeg_task.cancel()
            try:
                await self._ffmpeg_task
            except asyncio.CancelledError:
                pass

        await self.connection.stop()
        await super().stop()

        logger.info("SRT input stopped")

    def get_stats(self) -> SRTMetricsSnapshot:
        """Get SRT connection statistics"""
        return self.connection.get_stats()

    def reset_stats(self) -> None:
        """Reset SRT statistics"""
        self.connection.reset_stats()

    def get_stream_info(self) -> Dict[str, Any]:
        """Get detected stream information"""
        return {
            **self._stream_info,
            "srt_mode": self.config.mode.value,
            "srt_host": self.config.host,
            "srt_port": self.config.port,
            "srt_latency_ms": self.config.latency_ms,
        }

    @property
    def is_connected(self) -> bool:
        return self.connection.is_connected

    @property
    def connection_state(self) -> str:
        return self.connection.state.value
