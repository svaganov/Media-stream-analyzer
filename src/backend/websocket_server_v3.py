"""WebSocket server v3 with full StreamPipeline integration.

SRT + FFmpeg + Audio Analyzer + Video Keyframes in one pipeline.
"""
import asyncio
import json
import logging
import time
from typing import Dict, Set, Optional, Any

import websockets
from websockets.server import WebSocketServerProtocol

from .config import config, WebSocketConfig
from .stream_pipeline import StreamPipeline, PipelineConfig

logger = logging.getLogger(__name__)


class WebSocketServerV3:
    """WebSocket server with full stream pipeline including video."""

    def __init__(self, ws_config: Optional[WebSocketConfig] = None):
        self.ws_config = ws_config or config.websocket
        self.pipeline: Optional[StreamPipeline] = None
        self._server: Optional[websockets.WebSocketServer] = None
        self._clients: Set[WebSocketServerProtocol] = set()

    async def _handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """Handle client connection."""
        client_id = id(websocket)
        logger.info(f"New client: {websocket.remote_address} (id={client_id})")

        self._clients.add(websocket)

        # Send cached data if pipeline is running
        if self.pipeline:
            cached = self.pipeline.get_cached_data()
            for msg_type, data in cached.items():
                if data:
                    await websocket.send(json.dumps({
                        "type": msg_type,
                        "data": data
                    }))

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
            self._clients.discard(websocket)
            logger.info(f"Client disconnected. Total: {len(self._clients)}")

    async def _handle_message(self, client: WebSocketServerProtocol, data: Dict[str, Any]):
        """Handle client message."""
        action = data.get("action")

        if action == "connect":
            url = data.get("url", config.srt.url)
            protocol = data.get("protocol", "srt")
            mode = data.get("mode", "caller")
            latency = data.get("latency", config.srt.latency)
            extract_keyframes = data.get("extract_keyframes", True)

            await self._start_pipeline(url, mode, latency, extract_keyframes)

            await client.send(json.dumps({
                "type": "connection_status",
                "connected": self.pipeline.is_connected if self.pipeline else False,
                "url": url
            }))

        elif action == "disconnect":
            await self._stop_pipeline()
            await client.send(json.dumps({
                "type": "connection_status", "connected": False
            }))

        elif action == "reset":
            if self.pipeline and self.pipeline.audio_analyzer:
                self.pipeline.audio_analyzer.reset()
            await client.send(json.dumps({"type": "reset_complete"}))

        elif action == "get_status":
            await client.send(json.dumps({
                "type": "status",
                "connected": self.pipeline.is_connected if self.pipeline else False,
                "clients": len(self._clients)
            }))

        elif action == "set_latency":
            latency = data.get("latency", 120)
            config.srt.latency = latency
            await client.send(json.dumps({
                "type": "latency_set", "latency": latency
            }))

        else:
            await client.send(json.dumps({
                "type": "error", "message": f"Unknown action: {action}"
            }))

    async def _start_pipeline(self, url: str, mode: str, latency: int, extract_keyframes: bool = True):
        """Start stream pipeline."""
        if self.pipeline:
            await self.pipeline.stop()

        pipeline_config = PipelineConfig(
            srt_url=url,
            srt_mode=mode,
            srt_latency_ms=latency,
            extract_keyframes=extract_keyframes
        )

        self.pipeline = StreamPipeline(pipeline_config)

        # Setup callbacks
        self.pipeline.on_srt_stats(self._broadcast_srt_stats)
        self.pipeline.on_audio_analysis(self._broadcast_audio_analysis)
        self.pipeline.on_loudness_history(self._broadcast_loudness_history)
        self.pipeline.on_keyframe(self._broadcast_keyframe)
        self.pipeline.on_gop(self._broadcast_gop)
        self.pipeline.on_error(self._broadcast_error)

        started = await self.pipeline.start()

        if not started:
            logger.error("Failed to start pipeline")
            self.pipeline = None

    async def _stop_pipeline(self):
        """Stop stream pipeline."""
        if self.pipeline:
            await self.pipeline.stop()
            self.pipeline = None

    # Broadcast helpers
    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast to all clients."""
        if not self._clients:
            return

        json_msg = json.dumps(message)
        disconnected = set()

        for client in self._clients:
            try:
                await client.send(json_msg)
            except Exception:
                disconnected.add(client)

        self._clients -= disconnected

    def _broadcast_srt_stats(self, stats: Dict[str, Any]):
        asyncio.create_task(self._broadcast({
            "type": "srt_stats", "data": stats
        }))

    def _broadcast_audio_analysis(self, analysis: Dict[str, Any]):
        asyncio.create_task(self._broadcast({
            "type": "audio_analysis", "data": analysis
        }))

    def _broadcast_loudness_history(self, history: List[float]):
        asyncio.create_task(self._broadcast({
            "type": "loudness_history",
            "data": {"values": history, "window_seconds": 60}
        }))

    def _broadcast_keyframe(self, keyframe: Dict[str, Any]):
        asyncio.create_task(self._broadcast({
            "type": "keyframe", "data": keyframe
        }))

    def _broadcast_gop(self, gop: Dict[str, Any]):
        asyncio.create_task(self._broadcast({
            "type": "gop", "data": gop
        }))

    def _broadcast_error(self, message: str):
        asyncio.create_task(self._broadcast({
            "type": "error", "message": message
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

        logger.info(f"Server started: ws://{self.ws_config.host}:{self.ws_config.port}")

    async def stop(self):
        """Stop server."""
        await self._stop_pipeline()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Server stopped")

    async def run_forever(self):
        """Run forever."""
        await self.start()
        await asyncio.Future()
