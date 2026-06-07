"""Tests for video keyframe extractor."""
import pytest
import numpy as np
from unittest.mock import Mock, patch

from analyzers.video.keyframe_extractor import (
    VideoKeyframeExtractor, KeyframeImage, VideoFrame, 
    FrameType, GOPStructure
)


class TestVideoKeyframeExtractor:
    """Test video keyframe extractor."""

    def test_init(self):
        extractor = VideoKeyframeExtractor()
        assert extractor._running is False
        assert extractor._frame_count == 0

    def test_callbacks(self):
        extractor = VideoKeyframeExtractor()
        callback = Mock()
        extractor.on_keyframe(callback)

        image = KeyframeImage(
            timestamp=0,
            frame_number=1,
            width=320,
            height=180,
            rgb_data=np.zeros((180, 320, 3), dtype=np.uint8)
        )
        extractor._notify_keyframe(image)

        callback.assert_called_once()

    def test_gop_structure(self):
        frames = [
            VideoFrame(0, FrameType.IDR, 1, 1920, 1080, True, 0, 0),
            VideoFrame(0.04, FrameType.B, 2, 1920, 1080, False, 3600, 3600),
            VideoFrame(0.08, FrameType.B, 3, 1920, 1080, False, 7200, 7200),
            VideoFrame(0.12, FrameType.P, 4, 1920, 1080, False, 10800, 10800),
            VideoFrame(0.16, FrameType.B, 5, 1920, 1080, False, 14400, 14400),
            VideoFrame(0.20, FrameType.B, 6, 1920, 1080, False, 18000, 18000),
            VideoFrame(0.24, FrameType.P, 7, 1920, 1080, False, 21600, 21600),
        ]

        gop = GOPStructure(
            frames=frames,
            gop_size=7,
            idr_interval=7,
            has_b_frames=True
        )

        assert gop.gop_size == 7
        assert gop.idr_count == 1
        assert gop.i_count == 1
        assert gop.p_count == 2
        assert gop.b_count == 4
        assert gop.has_b_frames is True
        assert gop.pattern == "IDRBBPBBP"

    def test_gop_counts(self):
        frames = [
            VideoFrame(0, FrameType.IDR, 1, 1920, 1080, True, 0, 0),
            VideoFrame(0.04, FrameType.P, 2, 1920, 1080, False, 3600, 3600),
            VideoFrame(0.08, FrameType.P, 3, 1920, 1080, False, 7200, 7200),
        ]

        gop = GOPStructure(frames=frames, gop_size=3, idr_interval=3, has_b_frames=False)

        assert gop.idr_count == 1
        assert gop.p_count == 2
        assert gop.b_count == 0
        assert gop.has_b_frames is False

    def test_video_frame_to_dict(self):
        frame = VideoFrame(
            timestamp=1.5,
            frame_type=FrameType.IDR,
            frame_number=10,
            width=1920,
            height=1080,
            is_keyframe=True,
            pts=135000,
            dts=135000
        )

        data = frame.to_dict()
        assert data["frame_type"] == "IDR"
        assert data["frame_number"] == 10
        assert data["width"] == 1920
        assert data["is_keyframe"] is True

    def test_keyframe_image(self):
        rgb = np.random.randint(0, 255, (180, 320, 3), dtype=np.uint8)
        image = KeyframeImage(
            timestamp=0.5,
            frame_number=5,
            width=320,
            height=180,
            rgb_data=rgb
        )

        assert image.width == 320
        assert image.height == 180
        assert image.rgb_data.shape == (180, 320, 3)


class TestFrameType:
    """Test frame type enum."""

    def test_values(self):
        assert FrameType.IDR == 1
        assert FrameType.I == 2
        assert FrameType.P == 3
        assert FrameType.B == 4

    def test_names(self):
        assert FrameType.IDR.name == "IDR"
        assert FrameType.I.name == "I"
        assert FrameType.P.name == "P"
        assert FrameType.B.name == "B"
