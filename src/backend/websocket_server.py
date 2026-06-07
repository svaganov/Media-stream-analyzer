"""WebSocket server for real-time stream data broadcasting."""
import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any
from dataclasses import asdict

import websockets
from websockets.server import WebSocketServerProtocol

from .config import config, WebSocketConfig
from .srt_client import SRTClient, SRTStats
from ..analyzers.audio.audio_analyzer import AudioAnalyzer, AudioAnalysis
from ..analyzers.video.stream_decoder import StreamDecoder, StreamInfo

logger = logging.getLogger(__name__)


class StreamManager:
    """Manages stream connections and data distribution."""

    def __init__(self):
        self.srt_client: Optional[SRTClient] = None
        self.decoder: Optional[StreamDecoder] = None
        self.audio_analyzer: Optional[AudioAnalyzer] = None

        self._connected_clients: Set[WebSocketServerProtocol] = set()
        self._running = False
        self._stream_info: Optional[StreamInfo] = None

        # Data caches for new connections
        self._last_srt_stats: Optional[Dict] = None
        self._last_audio_analysis: Optional[Dict] = None
        self._last_stream_info: Optional[Dict] = None
        self._loudness_history: list[float] = []

    async def connect_stream(self, url: str, protocol: str = "srt", 
                            mode: str = "caller") -> bool:
        """Connect to a media stream."""
        try:
            logger.info(f"Connecting to {protocol} stream: {url}")

            # Initialize decoder
            self.decoder = StreamDecoder()

            # Probe stream info
            self._stream_info = await self.decoder.probe(url)
            if self._stream_info:
                self._last_stream_info = self._stream_info.to_dict()
                await self._broadcast({
                    "type": "stream_info",
                    "data": self._last_stream_info
                })

            # Initialize SRT client for SRT streams
            if protocol == "srt":
                host, port = self._parse_srt_url(url)
                self.srt_client = SRTClient(host=host, port=port, mode=mode)
                self.srt_client.on_stats(self._on_srt_stats)
                self.srt_client.on_error(self._on_srt_error)

                if not self.srt_client.connect():
                    logger.error("Failed to connect to SRT stream")
                    return False

            # Initialize audio analyzer
            self.audio_analyzer = AudioAnalyzer(
                sample_rate=config.ffmpeg.audio_sample_rate,
                channels=config.ffmpeg.audio_channels
            )
            self.audio_analyzer.on_analysis(self._on_audio_analysis)
            self.audio_analyzer.on_history(self._on_loudness_history)

            # Start stream decoding
            if self.decoder:
                await self.decoder.start(url, extract_audio=True, extract_video=False)
                self.decoder.on_audio(self._on_audio_frame)

            self._running = True
            logger.info("Stream connected successfully")
            return True

        except Exception as e:
            logger.error(f"Stream connection error: {e}")
            await self._broadcast({
                "type": "error",
                "message": str(e)
            })
            return False

    def _parse_srt_url(self, url: str) -> tuple[str, int]:
        """Parse SRT URL to get host and port."""
        # srt://host:port?param=value
        url = url.replace("srt://", "")
        if "?" in url:
            url = url.split("?")[0]
        host, port_str = url.split(":")
        return host, int(port_str)

    def _on_srt_stats(self, stats: SRTStats):
        """Handle SRT statistics."""
        self._last_srt_stats = stats.to_dict()
        asyncio.create_task(self._broadcast({
            "type": "srt_stats",
            "timestamp": time.time(),
            "data": self._last_srt_stats
        }))

    def _on_srt_error(self, message: str):
        """Handle SRT errors."""
        asyncio.create_task(self._broadcast({
            "type": "error",
            "source": "srt",
            "message": message
        }))

    def _on_audio_frame(self, frame):
        """Handle audio frame from decoder."""
        if self.audio_analyzer:
            self.audio_analyzer.process(frame.samples, frame.timestamp)

    def _on_audio_analysis(self, analysis: AudioAnalysis):
        """Handle audio analysis results."""
        self._last_audio_analysis = analysis.to_dict()
        asyncio.create_task(self._broadcast({
            "type": "audio_analysis",
            "timestamp": time.time(),
            "data": self._last_audio_analysis
        }))

    def _on_loudness_history(self, history: list[float]):
        """Handle loudness history update."""
        self._loudness_history = history
        asyncio.create_task(self._broadcast({
            "type": "loudness_history",
            "data": {
                "values": history,
                "window_seconds": config.analyzer.loudness_history_window
            }
        }))

    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if not self._connected_clients:
            return

        json_msg = json.dumps(message)
        disconnected = set()

        for client in self._connected_clients:
            try:
                await client.send(json_msg)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.add(client)

        # Remove disconnected clients
        self._connected_clients -= disconnected

    async def add_client(self, client: WebSocketServerProtocol):
        """Add new client and send initial data."""
        self._connected_clients.add(client)
        logger.info(f"Client connected. Total: {len(self._connected_clients)}")

        # Send cached data to new client
        if self._last_stream_info:
            await client.send(json.dumps({
                "type": "stream_info",
                "data": self._last_stream_info
            }))

        if self._last_srt_stats:
            await client.send(json.dumps({
                "type": "srt_stats",
                "data": self._last_srt_stats
            }))

        if self._last_audio_analysis:
            await client.send(json.dumps({
                "type": "audio_analysis",
                "data": self._last_audio_analysis
            }))

        if self._loudness_history:
            await client.send(json.dumps({
                "type": "loudness_history",
                "data": {
                    "values": self._loudness_history,
                    "window_seconds": config.analyzer.loudness_history_window
                }
            }))

    def remove_client(self, client: WebSocketServerProtocol):
        """Remove client."""
        self._connected_clients.discard(client)
        logger.info(f"Client disconnected. Total: {len(self._connected_clients)}")

    async def disconnect(self):
        """Disconnect from stream and cleanup."""
        self._running = False

        if self.srt_client:
            self.srt_client.disconnect()

        if self.decoder:
            await self.decoder.stop()

        logger.info("Stream disconnected")


class WebSocketServer:
    """WebSocket server for Media Stream Analyzer."""

    def __init__(self, ws_config: Optional[WebSocketConfig] = None):
        self.ws_config = ws_config or config.websocket
        self.stream_manager = StreamManager()
        self._server: Optional[websockets.WebSocketServer] = None

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connection."""
        client_id = id(websocket)
        logger.info(f"New connection from {websocket.remote_address} (id={client_id})")

        await self.stream_manager.add_client(websocket)

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {client_id}")
        finally:
            self.stream_manager.remove_client(websocket)

    async def _handle_message(self, client: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle client message."""
        action = data.get("action")

        if action == "connect":
            url = data.get("url", "")
            protocol = data.get("protocol", "srt")
            mode = data.get("mode", "caller")

            success = await self.stream_manager.connect_stream(url, protocol, mode)
            await client.send(json.dumps({
                "type": "connection_status",
                "connected": success,
                "url": url,
                "protocol": protocol
            }))

        elif action == "disconnect":
            await self.stream_manager.disconnect()
            await client.send(json.dumps({
                "type": "connection_status",
                "connected": False
            }))

        elif action == "set_window":
            window = data.get("window", "5m")
            await client.send(json.dumps({
                "type": "window_set",
                "window": window
            }))

        elif action == "reset":
            if self.stream_manager.audio_analyzer:
                self.stream_manager.audio_analyzer.reset()
            await client.send(json.dumps({
                "type": "reset_complete"
            }))

        elif action == "get_status":
            await client.send(json.dumps({
                "type": "status",
                "connected": self.stream_manager.srt_client.is_connected if self.stream_manager.srt_client else False,
                "clients": len(self.stream_manager._connected_clients)
            }))

        else:
            await client.send(json.dumps({
                "type": "error",
                "message": f"Unknown action: {action}"
            }))

    async def start(self):
        """Start WebSocket server."""
        logger.info(f"Starting WebSocket server on {self.ws_config.host}:{self.ws_config.port}")

        self._server = await websockets.serve(
            self._handle_client,
            self.ws_config.host,
            self.ws_config.port,
            ping_interval=self.ws_config.ping_interval,
            ping_timeout=self.ws_config.ping_timeout
        )

        logger.info(f"WebSocket server started. ws://{self.ws_config.host}:{self.ws_config.port}")

    async def stop(self):
        """Stop WebSocket server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        await self.stream_manager.disconnect()
        logger.info("WebSocket server stopped")

    async def run_forever(self):
        """Run server indefinitely."""
        await self.start()
        await asyncio.Future()  # Run forever
