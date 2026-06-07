"""Tests for FFmpeg audio decoder."""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import subprocess

from analyzers.audio.ffmpeg_audio_decoder import FFmpegAudioDecoder, AudioDecoderConfig


class TestFFmpegAudioDecoder:
    """Test FFmpeg audio decoder."""

    def test_init(self):
        config = AudioDecoderConfig(input_url="srt://192.168.1.100:9000")
        decoder = FFmpegAudioDecoder(config)
        assert decoder.config.input_url == "srt://192.168.1.100:9000"

    def test_bytes_per_sample(self):
        config = AudioDecoderConfig()
        assert config.bytes_per_sample == 4  # float32

    def test_bytes_per_frame(self):
        config = AudioDecoderConfig(block_size=1024, channels=2)
        assert config.bytes_per_frame == 1024 * 2 * 4  # 8192

    def test_callbacks(self):
        decoder = FFmpegAudioDecoder()
        callback = Mock()
        decoder.on_audio(callback)

        # Simulate audio notification
        samples = np.random.randn(2, 1024).astype(np.float32) * 0.1
        decoder._notify_audio(samples, 0.0)

        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0].shape == (2, 1024)  # samples
        assert args[1] == 0.0  # timestamp

    def test_notify_error(self):
        decoder = FFmpegAudioDecoder()
        callback = Mock()
        decoder.on_error(callback)

        decoder._notify_error("Test error")
        callback.assert_called_once_with("Test error")

    @patch('subprocess.Popen')
    def test_start_success(self, mock_popen):
        mock_process = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_popen.return_value = mock_process

        decoder = FFmpegAudioDecoder()
        result = decoder.start()

        assert result is True
        mock_popen.assert_called_once()

        # Check FFmpeg command
        cmd = mock_popen.call_args[0][0]
        assert "ffmpeg" in cmd[0]
        assert "-i" in cmd
        assert "pipe:1" in cmd

    @patch('subprocess.Popen')
    def test_start_ffmpeg_not_found(self, mock_popen):
        mock_popen.side_effect = FileNotFoundError()

        decoder = FFmpegAudioDecoder()
        result = decoder.start()

        assert result is False


class TestAudioDecoderConfig:
    """Test audio decoder configuration."""

    def test_defaults(self):
        config = AudioDecoderConfig()
        assert config.sample_rate == 48000
        assert config.channels == 2
        assert config.sample_format == "f32le"

    def test_custom(self):
        config = AudioDecoderConfig(
            input_url="srt://10.0.0.1:5000",
            sample_rate=44100,
            channels=1
        )
        assert config.input_url == "srt://10.0.0.1:5000"
        assert config.sample_rate == 44100
        assert config.channels == 1
