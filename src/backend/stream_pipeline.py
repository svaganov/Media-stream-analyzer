"""Stream Pipeline v2: SRT + FFmpeg + Audio + Video + Alerts + Metadata.

Full pipeline with alert system and stream metadata parsing.
"""
import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass

import numpy as np

from .libsrt_native import get_srt_lib, SRTNativeStats
from .srt_connection import SRTConnection, SRTConnectionConfig, SRTMode
from .alert_manager import AlertManager, AlertThreshold, Alert
from ..analyzers.audio.ffmpeg_audio_decoder import FFmpegAudioDecoder, AudioDecoderConfig
from ..analyzers.audio.audio_analyzer import AudioAnalyzer, AudioAnalysis
from ..analyzers.video.keyframe_extractor import VideoKeyframeExtractor, KeyframeImage, GOPStructure
from ..analyzers.video.stream_metadata import StreamMetadataParser

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    srt_url: str = "srt://127.0.0.1:9000"
    srt_mode: str = "caller"
    srt_latency_ms: int = 120

    audio_sample_rate: int = 48000
    audio_channels: int = 2

    extract_keyframes: bool = True
    keyframe_width: int = 320

    enable_alerts: bool = True
    alert_thresholds: Optional[AlertThreshold] = None

    stats_interval: float = 1.0


class StreamPipeline:
    """Complete stream analysis pipeline with alerts and metadata."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()

        # Components
        self.srt_connection: Optional[SRTConnection] = None
        self.audio_decoder: Optional[FFmpegAudioDecoder] = None
        self.audio_analyzer: Optional[AudioAnalyzer] = None
        self.keyframe_extractor: Optional[VideoKeyframeExtractor] = None
        self.alert_manager: Optional[AlertManager] = None
        self.metadata_parser: Optional[StreamMetadataParser] = None

        # State
        self._running = False
        self._connected = False

        # Callbacks
        self._srt_stats_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._audio_analysis_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._loudness_history_callbacks: List[Callable[[List[float]], None]] = []
        self._keyframe_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._gop_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._alert_resolve_callbacks: List[Callable[[str], None]] = []
        self._metadata_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self._error_callbacks: List[Callable[[str], None]] = []

        # Cached data
        self._last_srt_stats: Optional[Dict[str, Any]] = None
        self._last_audio_analysis: Optional[Dict[str, Any]] = None
        self._last_keyframe: Optional[Dict[str, Any]] = None
        self._last_gop: Optional[Dict[str, Any]] = None
        self._last_metadata: Optional[Dict[str, Any]] = None
        self._loudness_history: List[float] = []

        logger.info(f"StreamPipeline v2: {self.config.srt_url}")

    def on_srt_stats(self, callback): self._srt_stats_callbacks.append(callback)
    def on_audio_analysis(self, callback): self._audio_analysis_callbacks.append(callback)
    def on_loudness_history(self, callback): self._loudness_history_callbacks.append(callback)
    def on_keyframe(self, callback): self._keyframe_callbacks.append(callback)
    def on_gop(self, callback): self._gop_callbacks.append(callback)
    def on_alert(self, callback): self._alert_callbacks.append(callback)
    def on_alert_resolve(self, callback): self._alert_resolve_callbacks.append(callback)
    def on_metadata(self, callback): self._metadata_callbacks.append(callback)
    def on_error(self, callback): self._error_callbacks.append(callback)

    def _notify(self, callbacks, *args):
        for cb in callbacks:
            try:
                cb(*args)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def _notify_srt_stats(self, stats: Dict[str, Any]):
        self._last_srt_stats = stats
        self._notify(self._srt_stats_callbacks, stats)

        # Check alerts
        if self.alert_manager:
            self.alert_manager.check_srt_stats(stats)

    def _notify_audio_analysis(self, analysis: Dict[str, Any]):
        self._last_audio_analysis = analysis
        self._notify(self._audio_analysis_callbacks, analysis)

        # Check alerts
        if self.alert_manager:
            self.alert_manager.check_audio_analysis(analysis)

    def _notify_loudness_history(self, history: List[float]):
        self._loudness_history = history
        self._notify(self._loudness_history_callbacks, history)

    def _notify_keyframe(self, image: KeyframeImage):
        data = {
            "timestamp": image.timestamp,
            "frame_number": image.frame_number,
            "width": image.width,
            "height": image.height,
            "image_data": self._encode_image(image.rgb_data)
        }
        self._last_keyframe = data
        self._notify(self._keyframe_callbacks, data)

    def _notify_gop(self, gop: GOPStructure):
        data = gop.to_dict()
        self._last_gop = data
        self._notify(self._gop_callbacks, data)

    def _notify_metadata(self, metadata: Dict[str, Any]):
        self._last_metadata = metadata
        self._notify(self._metadata_callbacks, metadata)

    def _notify_alert(self, alert: Alert):
        self._notify(self._alert_callbacks, alert)

    def _notify_alert_resolve(self, alert_id: str):
        self._notify(self._alert_resolve_callbacks, alert_id)

    def _notify_error(self, message: str):
        logger.error(message)
        self._notify(self._error_callbacks, message)

    def _encode_image(self, rgb_data: np.ndarray) -> str:
        import base64
        from io import BytesIO
        from PIL import Image
        img = Image.fromarray(rgb_data)
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def start(self) -> bool:
        try:
            logger.info("Starting StreamPipeline v2...")

            # Initialize alert manager
            if self.config.enable_alerts:
                self.alert_manager = AlertManager(
                    self.config.alert_thresholds or AlertThreshold()
                )
                self.alert_manager.on_alert(self._notify_alert)
                self.alert_manager.on_resolve(self._notify_alert_resolve)
                logger.info("✅ Alert manager initialized")

            # Initialize metadata parser
            self.metadata_parser = StreamMetadataParser()

            # 1. Start SRT connection
            host, port = self._parse_srt_url(self.config.srt_url)
            srt_mode = SRTMode.CALLER if self.config.srt_mode == "caller" else SRTMode.LISTENER

            srt_config = SRTConnectionConfig(
                host=host, port=port, mode=srt_mode,
                latency_ms=self.config.srt_latency_ms
            )

            self.srt_connection = SRTConnection(srt_config)
            self.srt_connection.on_stats(self._handle_srt_stats)
            self.srt_connection.on_state_change(self._handle_srt_state)
            self.srt_connection.on_error(self._handle_srt_error)

            loop = asyncio.get_event_loop()
            connected = await loop.run_in_executor(None, self.srt_connection.connect)

            if not connected:
                self._notify_error("Failed to connect to SRT stream")
                return False

            logger.info("✅ SRT connection established")

            # 2. Start FFmpeg audio decoder
            decoder_config = AudioDecoderConfig(
                input_url=self.config.srt_url,
                sample_rate=self.config.audio_sample_rate,
                channels=self.config.audio_channels
            )

            self.audio_decoder = FFmpegAudioDecoder(decoder_config)
            self.audio_decoder.on_audio(self._handle_audio_data)
            self.audio_decoder.on_error(self._handle_decoder_error)
            self.audio_decoder.on_info(self._handle_decoder_info)

            decoder_started = await self.audio_decoder.start_async()

            if not decoder_started:
                self._notify_error("Failed to start FFmpeg audio decoder")
                await self._stop_srt()
                return False

            logger.info("✅ FFmpeg audio decoder started")

            # 3. Initialize audio analyzer
            self.audio_analyzer = AudioAnalyzer(
                sample_rate=self.config.audio_sample_rate,
                channels=self.config.audio_channels
            )
            self.audio_analyzer.on_analysis(self._handle_audio_analysis)
            self.audio_analyzer.on_history(self._handle_loudness_history)

            logger.info("✅ Audio analyzer initialized")

            # 4. Start video keyframe extractor
            if self.config.extract_keyframes:
                self.keyframe_extractor = VideoKeyframeExtractor()
                self.keyframe_extractor.on_keyframe(self._notify_keyframe)
                self.keyframe_extractor.on_gop(self._notify_gop)
                self.keyframe_extractor.on_error(self._handle_video_error)

                keyframe_started = await self.keyframe_extractor.start_async(self.config.srt_url)

                if keyframe_started:
                    logger.info("✅ Video keyframe extractor started")
                else:
                    logger.warning("⚠️ Keyframe extraction failed")

            self._running = True
            self._connected = True

            logger.info("✅ StreamPipeline v2 fully started")
            return True

        except Exception as e:
            self._notify_error(f"Pipeline start error: {e}")
            await self.stop()
            return False

    async def stop(self):
        logger.info("Stopping StreamPipeline v2...")
        self._running = False
        self._connected = False

        if self.keyframe_extractor:
            await self.keyframe_extractor.stop_async()
            self.keyframe_extractor = None

        if self.audio_decoder:
            await self.audio_decoder.stop_async()
            self.audio_decoder = None

        await self._stop_srt()

        self.audio_analyzer = None
        self.alert_manager = None
        self.metadata_parser = None

        logger.info("StreamPipeline v2 stopped")

    async def _stop_srt(self):
        if self.srt_connection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.srt_connection.disconnect)
            self.srt_connection = None

    def _handle_srt_stats(self, stats: SRTNativeStats):
        data = {
            "timestamp": time.time(),
            **stats.to_dict(),
            "uptime_seconds": round(self.srt_connection.uptime_seconds, 1) if self.srt_connection else 0,
            "state": self.srt_connection.get_state() if self.srt_connection else "unknown"
        }
        self._notify_srt_stats(data)

    def _handle_srt_state(self, state: str):
        if state == "disconnected":
            self._connected = False

    def _handle_srt_error(self, message: str):
        self._notify_error(f"SRT: {message}")

    def _handle_audio_data(self, samples: np.ndarray, timestamp: float):
        if self.audio_analyzer:
            self.audio_analyzer.process(samples, timestamp)

    def _handle_audio_analysis(self, analysis: AudioAnalysis):
        self._notify_audio_analysis(analysis.to_dict())

    def _handle_loudness_history(self, history: List[float]):
        self._notify_loudness_history(history)

    def _handle_decoder_error(self, message: str):
        self._notify_error(f"Decoder: {message}")

    def _handle_decoder_info(self, info: Dict[str, Any]):
        # Parse metadata from FFmpeg output
        if self.metadata_parser:
            if isinstance(info, dict) and "info" in info:
                self.metadata_parser.parse_line(info["info"])
                metadata = self.metadata_parser.get_stream_info()
                if metadata["video"]["codec"] or metadata["audio"]["codec"]:
                    self._notify_metadata(metadata)

    def _handle_video_error(self, message: str):
        self._notify_error(f"Video: {message}")

    def _parse_srt_url(self, url: str) -> tuple[str, int]:
        url = url.replace("srt://", "")
        if "?" in url:
            url = url.split("?")[0]
        host, port_str = url.split(":")
        return host, int(port_str)

    def get_cached_data(self) -> Dict[str, Any]:
        return {
            "srt_stats": self._last_srt_stats,
            "audio_analysis": self._last_audio_analysis,
            "loudness_history": self._loudness_history,
            "keyframe": self._last_keyframe,
            "gop": self._last_gop,
            "metadata": self._last_metadata,
        }

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_connected(self) -> bool:
        return self._connected
