"""Tests for stream metadata parser."""
import pytest

from analyzers.video.stream_metadata import StreamMetadataParser, VideoStreamInfo, AudioStreamInfo


class TestStreamMetadataParser:
    """Test stream metadata parser."""

    @pytest.fixture
    def parser(self):
        return StreamMetadataParser()

    def test_parse_video_stream(self, parser):
        line = "Stream #0:0: Video: h264 (High 4.2), yuv420p(tv, bt709, progressive), 1920x1080 [SAR 1:1 DAR 16:9], 5000 kb/s, 25 fps, 25 tbr, 90k tbn, 50 tbc"
        result = parser.parse_line(line)

        assert result is True
        assert parser.video_info.codec == "h264"
        assert parser.video_info.profile == "High 4.2"
        assert parser.video_info.width == 1920
        assert parser.video_info.height == 1080
        assert parser.video_info.frame_rate == 25.0
        assert parser.video_info.bitrate == 5000000
        assert parser.video_info.color_space == "yuv420p"

    def test_parse_audio_stream(self, parser):
        line = "Stream #0:1: Audio: aac (LC), 48000 Hz, stereo, fltp, 128 kb/s"
        result = parser.parse_line(line)

        assert result is True
        assert parser.audio_info.codec == "aac"
        assert parser.audio_info.sample_rate == 48000
        assert parser.audio_info.channels == 2
        assert parser.audio_info.channel_layout == "stereo"
        assert parser.audio_info.bitrate == 128000
        assert parser.audio_info.sample_format == "fltp"

    def test_parse_duration(self, parser):
        line = "Duration: 00:05:23.45, start: 0.000000, bitrate: 8500 kb/s"
        result = parser.parse_line(line)

        assert result is True
        assert parser.container_info.duration == 5 * 60 + 23.45

    def test_parse_format_srt(self, parser):
        line = "Input #0, srt, from 'srt://192.168.1.100:9000'"
        result = parser.parse_line(line)

        assert result is True
        assert parser.container_info.format == "SRT"

    def test_parse_format_rtmp(self, parser):
        line = "Input #0, flv, from 'rtmp://server/live/stream'"
        result = parser.parse_line(line)

        assert result is True
        assert parser.container_info.format == "RTMP"

    def test_get_stream_info(self, parser):
        parser.video_info.codec = "h264"
        parser.video_info.width = 1920
        parser.audio_info.codec = "aac"
        parser.audio_info.sample_rate = 48000

        info = parser.get_stream_info()
        assert info["video"]["codec"] == "h264"
        assert info["video"]["width"] == 1920
        assert info["audio"]["codec"] == "aac"
        assert info["audio"]["sample_rate"] == 48000

    def test_reset(self, parser):
        parser.video_info.codec = "h264"
        parser.reset()

        assert parser.video_info.codec == ""
        assert parser.audio_info.codec == ""


class TestVideoStreamInfo:
    """Test video stream info dataclass."""

    def test_defaults(self):
        info = VideoStreamInfo()
        assert info.codec == ""
        assert info.width == 0
        assert info.height == 0
        assert info.frame_rate == 0.0

    def test_to_dict(self):
        info = VideoStreamInfo(
            codec="h264",
            width=1920,
            height=1080,
            frame_rate=25.0
        )
        data = info.to_dict()
        assert data["codec"] == "h264"
        assert data["width"] == 1920


class TestAudioStreamInfo:
    """Test audio stream info dataclass."""

    def test_defaults(self):
        info = AudioStreamInfo()
        assert info.codec == ""
        assert info.sample_rate == 48000
        assert info.channels == 2
