"""Tests for Silence Detector — Sprint 1."""

import numpy as np
import pytest
from v2.src.analyzers.audio.silence_detector import SilenceDetector


class TestSilenceDetector:
    """Test silence detector."""

    def test_silence_detected(self, silence):
        detector = SilenceDetector(threshold_db=-60, duration_sec=0.5)
        result = detector.process(silence)
        assert result["active"] is True
        assert result["duration_sec"] > 0.0

    def test_no_silence_with_signal(self, sine_1khz):
        detector = SilenceDetector(threshold_db=-60, duration_sec=0.5)
        result = detector.process(sine_1khz)
        assert result["active"] is False
        assert result["duration_sec"] == 0.0

    def test_threshold_boundary(self):
        detector = SilenceDetector(threshold_db=-30, duration_sec=0.1)
        
        # Signal at -40 dBFS (below -30 threshold)
        sr = 48000
        duration = 0.5
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        amplitude = 10 ** (-40 / 20)
        mono = amplitude * np.sin(2 * np.pi * 1000 * t)
        samples = np.stack([mono, mono]).astype(np.float32)
        
        result = detector.process(samples)
        assert result["active"] is True

    def test_threshold_not_crossed(self):
        detector = SilenceDetector(threshold_db=-60, duration_sec=0.5)
        
        # Signal at -40 dBFS (above -60 threshold)
        sr = 48000
        duration = 0.5
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        amplitude = 10 ** (-40 / 20)
        mono = amplitude * np.sin(2 * np.pi * 1000 * t)
        samples = np.stack([mono, mono]).astype(np.float32)
        
        result = detector.process(samples)
        assert result["active"] is False

    def test_duration_requirement(self):
        detector = SilenceDetector(threshold_db=-60, duration_sec=1.0)
        
        # Only 0.5 seconds of silence
        sr = 48000
        silence_short = np.zeros((2, sr // 2), dtype=np.float32)
        result = detector.process(silence_short)
        assert result["active"] is False

    def test_reset(self, silence):
        detector = SilenceDetector()
        detector.process(silence)
        detector.reset()
        result = detector.to_dict()
        assert result["active"] is False
        assert result["duration_sec"] == 0.0
