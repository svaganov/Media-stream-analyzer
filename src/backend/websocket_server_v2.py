"""WebSocket server v2 with native SRT integration.

Uses libsrt_native for real-time SRT statistics.
"""
import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any
from dataclasses import asdict

import websockets
from websockets.server import WebSocketServerProtocol

from .config import config, WebSocketConfig
from .srt_connection import SRTConnection, SRTConnectionConfig, SRTMode, SRTNativeStats
from .libsrt_native import SRT_SOCKSTATUS
from ..analyzers.audio.audio_analyzer import AudioAnalyzer, AudioAnalysis
from ..analyzers.video.stream_decoder import StreamDecoder, StreamInfo

logger = logging.getLogger(__name__)


class StreamManagerV2:
    """Stream manager with native SRT support."""

    def __init__(self):
        self.srt_connection: Optional[SRTConnection] = None
        self.decoder: Optional[StreamDecoder] = None
        self.audio_analyzer: Optional[AudioAnalyzer] = None

        self._connected_clients: Set[WebSocketServerProtocol] = set()
        self._running = False
        self._stream_info: Optional[StreamInfo] = None

        # Data caches
        self._last_srt_stats: Optional[Dict] = None
        self._last_audio_analysis: Optional[Dict] = None
        self._last_stream_info: Optional[Dict] = None
        self._loudness_history: list[float] = []

        # Receive loop
        self._receive_task: Optional[asyncio.Task] = None

    async def connect_stream(self, url: str, protocol: str = "srt", 
                            mode: str = "caller") -> bool:
        """Connect to stream using native SRT."""
        try:
            logger.info(f"Connecting to {protocol} stream: {url}")

            if protocol == "srt":
                # Parse URL
                host, port = self._parse_srt_url(url)
                srt_mode = SRTMode.CALLER if mode == "caller" else SRTMode.LISTENER

                # Create SRT connection
                srt_config = SRTConnectionConfig(
                    host=host,
                    port=port,
                    mode=srt_mode,
                    latency_ms=config.srt.latency
                )

                self.srt_connection = SRTConnection(srt_config)
                self.srt_connection.on_stats(self._on_srt_stats)
                self.srt_connection.on_state_change(self._on_srt_state)
                self.srt_connection.on_error(self._on_srt_error)

                # Connect (blocking, run in thread)
                loop = asyncio.get_event_loop()
                connected = await loop.run_in_executor(None, self.srt_connection.connect)

                if not connected:
                    logger.error("Failed to connect to SRT stream")
                    return False

                # Start receive loop
                self._receive_task = asyncio.create_task(self._receive_loop())

            # Initialize audio analyzer
            self.audio_analyzer = AudioAnalyzer(
                sample_rate=config.ffmpeg.audio_sample_rate,
                channels=config.ffmpeg.audio_channels
            )
            self.audio_analyzer.on_analysis(self._on_audio_analysis)
            self.audio_analyzer.on_history(self._on_loudness_history)

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
        """Parse SRT URL."""
        url = url.replace("srt://", "")
        if "?" in url:
            url = url.split("?")[0]
        host, port_str = url.split(":")
        return host, int(port_str)

    async def _receive_loop(self):
        """Receive data from SRT in background."""
        while self._running and self.srt_connection and self.srt_connection.is_connected:
            try:
                # Receive data (run in thread to not block)
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, self.srt_connection.receive, 188 * 7)

                if data:
                    # Process MPEG-TS data
                    # TODO: Extract audio frames and feed to analyzer
                    pass

            except Exception as e:
                logger.error(f"Receive loop error: {e}")
                await asyncio.sleep(0.1)

    def _on_srt_stats(self, stats: SRTNativeStats):
        """Handle SRT statistics."""
        self._last_srt_stats = {
            "timestamp": time.time(),
            **stats.to_dict(),
            "uptime_seconds": round(self.srt_connection.uptime_seconds, 1) if self.srt_connection else 0,
            "state": self.srt_connection.get_state() if self.srt_connection else "unknown"
        }
        asyncio.create_task(self._broadcast({
            "type": "srt_stats",
            "data": self._last_srt_stats
        }))

    def _on_srt_state(self, state: str):
        """Handle SRT state change."""
        asyncio.create_task(self._broadcast({
            "type": "connection_state",
            "state": state
        }))

    def _on_srt_error(self, message: str):
        """Handle SRT error."""
        asyncio.create_task(self._broadcast({
            "type": "error",
            "source": "srt",
            "message": message
        }))

    def _on_audio_analysis(self, analysis: AudioAnalysis):
        """Handle audio analysis."""
        self._last_audio_analysis = analysis.to_dict()
        asyncio.create_task(self._broadcast({
            "type": "audio_analysis",
            "timestamp": time.time(),
            "data": self._last_audio_analysis
        }))

    def _on_loudness_history(self, history: list[float]):
        """Handle loudness history."""
        self._loudness_history = history
        asyncio.create_task(self._broadcast({
            "type": "loudness_history",
            "data": {
                "values": history,
                "window_seconds": config.analyzer.loudness_history_window
            }
        }))

    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast to all clients."""
        if not self._connected_clients:
            return

        json_msg = json.dumps(message)
        disconnected = set()

        for client in self._connected_clients:
            try:
                await client.send(json_msg)
            except Exception:
                disconnected.add(client)

        self._connected_clients -= disconnected

    async def add_client(self, client: WebSocketServerProtocol):
        """Add new client."""
        self._connected_clients.add(client)
        logger.info(f"Client connected. Total: {len(self._connected_clients)}")

        # Send cached data
        for data in [self._last_stream_info, self._last_srt_stats, 
                      self._last_audio_analysis]:
            if data:
                await client.send(json.dumps(data))

        if self._loudness_history:
            await client.send(json.dumps({
                "type": "loudness_history",
                "data": {"values": self._loudness_history, "window_seconds": 60}
            }))

    def remove_client(self, client: WebSocketServerProtocol):
        """Remove client."""
        self._connected_clients.discard(client)
        logger.info(f"Client disconnected. Total: {len(self._connected_clients)}")

    async def disconnect(self):
        """Disconnect."""
        self._running = False

        if self._receive_task:
            self._receive_task.cancel()

        if self.srt_connection:
            await asyncio.get_event_loop().run_in_executor(None, self.srt_connection.disconnect)

        if self.decoder:
            await self.decoder.stop()

        logger.info("Stream disconnected")


class WebSocketServerV2:
    """WebSocket server with native SRT."""

    def __init__(self, ws_config: Optional[WebSocketConfig] = None):
        self.ws_config = ws_config or config.websocket
        self.stream_manager = StreamManagerV2()
        self._server: Optional[websockets.WebSocketServer] = None

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client."""
        client_id = id(websocket)
        logger.info(f"New connection: {websocket.remote_address} (id={client_id})")

        await self.stream_manager.add_client(websocket)

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error", "message": "Invalid JSON"
                    }))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.stream_manager.remove_client(websocket)

    async def _handle_message(self, client: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle message."""
        action = data.get("action")

        if action == "connect":
            url = data.get("url", "")
            protocol = data.get("protocol", "srt")
            mode = data.get("mode", "caller")

            success = await self.stream_manager.connect_stream(url, protocol, mode)
            await client.send(json.dumps({
                "type": "connection_status",
                "connected": success,
                "url": url
            }))

        elif action == "disconnect":
            await self.stream_manager.disconnect()
            await client.send(json.dumps({
                "type": "connection_status", "connected": False
            }))

        elif action == "get_stats":
            if self.stream_manager.srt_connection:
                stats = await asyncio.get_event_loop().run_in_executor(
                    None, self.stream_manager.srt_connection.get_stats
                )
                if stats:
                    await client.send(json.dumps({
                        "type": "srt_stats",
                        "data": stats.to_dict()
                    }))

        elif action == "get_state":
            if self.stream_manager.srt_connection:
                state = self.stream_manager.srt_connection.get_state()
                await client.send(json.dumps({
                    "type": "connection_state", "state": state
                }))

        elif action == "reset":
            if self.stream_manager.audio_analyzer:
                self.stream_manager.audio_analyzer.reset()
            await client.send(json.dumps({"type": "reset_complete"}))

        else:
            await client.send(json.dumps({
                "type": "error", "message": f"Unknown action: {action}"
            }))

    async def start(self):
        """Start server."""
        logger.info(f"Starting WebSocket server on {self.ws_config.host}:{self.ws_config.port}")

        self._server = await websockets.serve(
            self._handle_client,
            self.ws_config.host,
            self.ws_config.port,
            ping_interval=self.ws_config.ping_interval,
            ping_timeout=self.ws_config.ping_timeout
        )

        logger.info(f"Server started: ws://{self.ws_config.host}:{self.ws_config.port}")

    async def stop(self):
        """Stop server."""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        await self.stream_manager.disconnect()
        logger.info("Server stopped")

    async def run_forever(self):
        """Run forever."""
        await self.start()
        await asyncio.Future()
