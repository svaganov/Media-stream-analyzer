"""FFmpeg audio decoder for real-time stream analysis.

Reads audio from SRT/RTMP/any FFmpeg-supported input and outputs raw PCM.
"""
import asyncio
import logging
import subprocess
import numpy as np
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from enum import IntEnum

logger = logging.getLogger(__name__)


@dataclass
class AudioDecoderConfig:
    """Audio decoder configuration."""
    input_url: str = "srt://127.0.0.1:9000"
    sample_rate: int = 48000
    channels: int = 2
    sample_format: str = "f32le"  # float32 little-endian
    block_size: int = 1024  # samples per read
    ffmpeg_path: str = "ffmpeg"

    @property
    def bytes_per_sample(self) -> int:
        return 4  # float32 = 4 bytes

    @property
    def bytes_per_frame(self) -> int:
        return self.block_size * self.channels * self.bytes_per_sample


class FFmpegAudioDecoder:
    """FFmpeg-based real-time audio decoder.

    Launches FFmpeg subprocess with SRT input and raw PCM output.
    Reads stdout in real-time and feeds audio frames to callbacks.
    """

    def __init__(self, config: Optional[AudioDecoderConfig] = None):
        self.config = config or AudioDecoderConfig()

        self._process: Optional[subprocess.Popen] = None
        self._running = False
        self._connected = False

        # Callbacks
        self._audio_callbacks: List[Callable[[np.ndarray, float], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []
        self._info_callbacks: List[Callable[[Dict[str, Any]], None]] = []

        # Statistics
        self._total_samples_read: int = 0
        self._start_time: Optional[float] = None

        logger.info(f"FFmpegAudioDecoder: {self.config.input_url}")

    def on_audio(self, callback: Callable[[np.ndarray, float], None]):
        """Register audio data callback.

        Args:
            callback: Function(samples, timestamp) where samples is (channels, n_samples)
        """
        self._audio_callbacks.append(callback)

    def on_error(self, callback: Callable[[str], None]):
        """Register error callback."""
        self._error_callbacks.append(callback)

    def on_info(self, callback: Callable[[Dict[str, Any]], None]):
        """Register stream info callback."""
        self._info_callbacks.append(callback)

    def _notify_audio(self, samples: np.ndarray, timestamp: float):
        """Notify audio callbacks."""
        for cb in self._audio_callbacks:
            try:
                cb(samples, timestamp)
            except Exception as e:
                logger.error(f"Audio callback error: {e}")

    def _notify_error(self, message: str):
        """Notify error callbacks."""
        logger.error(message)
        for cb in self._error_callbacks:
            try:
                cb(message)
            except Exception:
                pass

    def _notify_info(self, info: Dict[str, Any]):
        """Notify info callbacks."""
        for cb in self._info_callbacks:
            try:
                cb(info)
            except Exception:
                pass

    def start(self) -> bool:
        """Start FFmpeg subprocess.

        Returns True if started successfully.
        """
        try:
            # Build FFmpeg command
            cmd = [
                self.config.ffmpeg_path,
                # Input
                "-i", self.config.input_url,
                # Audio output settings
                "-vn",  # no video
                "-acodec", "pcm_f32le",  # PCM float32 little-endian
                "-ar", str(self.config.sample_rate),  # sample rate
                "-ac", str(self.config.channels),  # channels
                "-f", "f32le",  # output format
                # Performance
                "-threads", "1",  # single thread for low latency
                "-fflags", "nobuffer+discardcorrupt",  # low latency
                "-flags", "low_delay",
                "-probesize", "32",  # small probe size
                "-analyzeduration", "0",  # minimal analysis
                # Output
                "pipe:1"
            ]

            logger.info(f"Starting FFmpeg: {' '.join(cmd)}")

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,  # unbuffered for real-time
            )

            self._running = True
            self._start_time = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0

            # Start reading threads
            import threading
            self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
            self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)

            self._stdout_thread.start()
            self._stderr_thread.start()

            self._connected = True
            logger.info("FFmpeg audio decoder started")
            return True

        except FileNotFoundError:
            self._notify_error(f"FFmpeg not found: {self.config.ffmpeg_path}")
            return False
        except Exception as e:
            self._notify_error(f"Failed to start FFmpeg: {e}")
            return False

    def _read_stdout(self):
        """Read audio data from FFmpeg stdout."""
        if not self._process or not self._process.stdout:
            return

        bytes_per_frame = self.config.bytes_per_frame
        bytes_per_sample = self.config.bytes_per_sample
        channels = self.config.channels
        sample_rate = self.config.sample_rate

        # Read buffer (slightly larger to handle partial reads)
        read_size = bytes_per_frame

        import time
        start_time = time.time()

        try:
            while self._running:
                raw_data = self._process.stdout.read(read_size)

                if not raw_data:
                    if self._process.poll() is not None:
                        break
                    continue

                # Ensure we have complete frames
                n_complete = (len(raw_data) // (channels * bytes_per_sample)) * channels * bytes_per_sample
                if n_complete == 0:
                    continue

                # Convert to numpy array
                samples = np.frombuffer(raw_data[:n_complete], dtype=np.float32)

                # Reshape to (channels, n_samples)
                n_samples = len(samples) // channels
                samples = samples.reshape(n_samples, channels).T

                # Calculate timestamp
                timestamp = self._total_samples_read / sample_rate
                self._total_samples_read += n_samples

                # Notify callbacks
                self._notify_audio(samples, timestamp)

        except Exception as e:
            self._notify_error(f"Audio read error: {e}")
        finally:
            self._connected = False
            logger.info("Audio reader stopped")

    def _read_stderr(self):
        """Read FFmpeg stderr for info and errors."""
        if not self._process or not self._process.stderr:
            return

        try:
            for line in iter(self._process.stderr.readline, b""):
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()

                # Parse useful info from FFmpeg output
                if "Stream #" in line_str and "Audio" in line_str:
                    self._notify_info({"type": "audio_stream", "info": line_str})
                elif "Stream #" in line_str and "Video" in line_str:
                    self._notify_info({"type": "video_stream", "info": line_str})
                elif "Duration" in line_str:
                    self._notify_info({"type": "duration", "info": line_str})
                elif "error" in line_str.lower() or "failed" in line_str.lower():
                    self._notify_error(f"FFmpeg: {line_str}")
                elif "speed=" in line_str:
                    # Processing speed indicator
                    pass

        except Exception as e:
            logger.error(f"Stderr read error: {e}")

    def stop(self):
        """Stop FFmpeg subprocess."""
        logger.info("Stopping FFmpeg audio decoder...")
        self._running = False
        self._connected = False

        if self._process:
            try:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait()
            except Exception as e:
                logger.error(f"Error stopping FFmpeg: {e}")

        logger.info("FFmpeg audio decoder stopped")

    async def start_async(self) -> bool:
        """Async version of start."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.start)

    async def stop_async(self):
        """Async version of stop."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.stop)

    @property
    def is_running(self) -> bool:
        """Check if decoder is running."""
        return self._running and self._connected

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        if self._start_time:
            return asyncio.get_event_loop().time() - self._start_time
        return 0.0
