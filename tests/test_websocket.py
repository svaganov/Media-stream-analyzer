"""Tests for WebSocket server."""
import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock

from backend.websocket_server import WebSocketServer, StreamManager


class TestStreamManager:
    """Test stream manager."""

    @pytest.fixture
    def manager(self):
        return StreamManager()

    def test_init(self, manager):
        assert manager.srt_client is None
        assert manager.decoder is None
        assert manager.audio_analyzer is None

    def test_parse_srt_url(self, manager):
        host, port = manager._parse_srt_url("srt://192.168.1.100:9000")
        assert host == "192.168.1.100"
        assert port == 9000

    def test_parse_srt_url_with_params(self, manager):
        host, port = manager._parse_srt_url("srt://192.168.1.100:9000?mode=listener")
        assert host == "192.168.1.100"
        assert port == 9000


class TestWebSocketServer:
    """Test WebSocket server."""

    @pytest.fixture
    def server(self):
        return WebSocketServer()

    def test_init(self, server):
        assert server.stream_manager is not None
        assert server.ws_config is not None
