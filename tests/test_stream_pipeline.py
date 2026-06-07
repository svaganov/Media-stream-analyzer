"""Tests for StreamPipeline."""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from backend.stream_pipeline import StreamPipeline, PipelineConfig


class TestStreamPipeline:
    """Test stream pipeline."""

    @pytest.fixture
    def pipeline(self):
        config = PipelineConfig(srt_url="srt://127.0.0.1:9000")
        return StreamPipeline(config)

    def test_init(self, pipeline):
        assert pipeline.config.srt_url == "srt://127.0.0.1:9000"
        assert pipeline.srt_connection is None
        assert pipeline.audio_decoder is None
        assert pipeline.audio_analyzer is None

    def test_parse_srt_url(self, pipeline):
        host, port = pipeline._parse_srt_url("srt://192.168.1.100:9000")
        assert host == "192.168.1.100"
        assert port == 9000

    def test_parse_srt_url_with_params(self, pipeline):
        host, port = pipeline._parse_srt_url("srt://192.168.1.100:9000?latency=120")
        assert host == "192.168.1.100"
        assert port == 9000

    def test_callbacks(self, pipeline):
        callback = Mock()
        pipeline.on_srt_stats(callback)

        test_stats = {"rtt_ms": 24.0, "bandwidth_mbps": 52.0}
        pipeline._notify_srt_stats(test_stats)

        callback.assert_called_once_with(test_stats)

    def test_cached_data_empty(self, pipeline):
        cached = pipeline.get_cached_data()
        assert cached["srt_stats"] is None
        assert cached["audio_analysis"] is None
        assert cached["loudness_history"] == []

    def test_cached_data_with_values(self, pipeline):
        pipeline._last_srt_stats = {"rtt": 24}
        pipeline._last_audio_analysis = {"dbfs": -12}
        pipeline._loudness_history = [-23, -22, -24]

        cached = pipeline.get_cached_data()
        assert cached["srt_stats"] == {"rtt": 24}
        assert cached["audio_analysis"] == {"dbfs": -12}
        assert cached["loudness_history"] == [-23, -22, -24]

    def test_is_running_false(self, pipeline):
        assert pipeline.is_running is False
        assert pipeline.is_connected is False


class TestPipelineConfig:
    """Test pipeline configuration."""

    def test_defaults(self):
        config = PipelineConfig()
        assert config.srt_url == "srt://127.0.0.1:9000"
        assert config.srt_mode == "caller"
        assert config.audio_sample_rate == 48000

    def test_custom(self):
        config = PipelineConfig(
            srt_url="srt://10.0.0.1:5000",
            srt_mode="listener",
            audio_channels=1
        )
        assert config.srt_url == "srt://10.0.0.1:5000"
        assert config.srt_mode == "listener"
        assert config.audio_channels == 1
