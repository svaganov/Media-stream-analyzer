"""Tests for True Peak Detector — Sprint 1."""

import numpy as np
import pytest
from v2.src.analyzers.audio.true_peak import TruePeakDetector


class TestTruePeakDetector:
    """Test True Peak detector."""

    def test_silence(self, silence):
        detector = TruePeakDetector()
        result = detector.process(silence)
        assert result["current"] == -70.0
        assert result["max"] == -70.0

    def test_sine_wave(self, sine_1khz):
        detector = TruePeakDetector()
        result = detector.process(sine_1khz)
        # True peak of sine wave is close to regular peak
        assert -25.0 < result["current"] < -15.0

    def test_full_scale(self, full_scale):
        detector = TruePeakDetector()
        result = detector.process(full_scale)
        # Full scale sine should be near 0 dBTP
        assert -3.0 < result["current"] <= 0.0

    def test_max_tracking(self, sine_1khz, full_scale):
        detector = TruePeakDetector()
        
        # Process quiet signal
        result1 = detector.process(sine_1khz)
        max1 = result1["max"]
        
        # Process loud signal
        result2 = detector.process(full_scale)
        max2 = result2["max"]
        
        # Max should increase
        assert max2 > max1
        assert max2 == pytest.approx(result2["current"], abs=0.1)

    def test_oversampling(self):
        detector = TruePeakDetector(oversampling=4)
        assert detector.oversampling == 4
        
        # Create signal with potential inter-sample peaks
        sr = 48000
        t = np.linspace(0, 1, sr, endpoint=False)
        # Square wave-ish signal
        samples = np.sign(np.sin(2 * np.pi * 1000 * t)) * 0.9
        stereo = np.stack([samples, samples]).astype(np.float32)
        
        result = detector.process(stereo)
        # With oversampling, may detect peaks > 0.9 linear
        assert result["current"] > -2.0  # Should be close to 0 dB

    def test_reset(self, full_scale):
        detector = TruePeakDetector()
        detector.process(full_scale)
        detector.reset()
        result = detector.to_dict()
        assert result["max"] == -70.0
