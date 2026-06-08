"""Tests for EBU R128 Calculator — Sprint 1."""

import numpy as np
import pytest
from v2.src.analyzers.audio.ebu_r128 import EBUR128Calculator


class TestEBUR128Calculator:
    """Test EBU R128 loudness calculator."""

    def test_silence(self, silence):
        calc = EBUR128Calculator()
        result = calc.process(silence)
        assert result["momentary"] == -70.0
        assert result["short_term"] == -70.0
        assert result["integrated"] == -70.0

    def test_sine_wave_loudness(self, sine_1khz):
        calc = EBUR128Calculator()
        # Process multiple seconds for stable reading
        for _ in range(5):
            result = calc.process(sine_1khz)
        
        # -20 dBFS sine should measure around -20 LUFS (simplified)
        assert -30.0 < result["momentary"] < -10.0
        assert -30.0 < result["short_term"] < -10.0

    def test_full_scale(self, full_scale):
        calc = EBUR128Calculator()
        for _ in range(5):
            result = calc.process(full_scale)
        
        # Full scale should be loud
        assert result["momentary"] > -10.0
        assert result["zone"] == "danger"

    def test_short_term_averaging(self, sine_1khz):
        calc = EBUR128Calculator()
        
        # Process 5 seconds
        results = []
        for _ in range(5):
            results.append(calc.process(sine_1khz))
        
        # Short-term should stabilize
        last = results[-1]
        assert last["short_term"] == pytest.approx(last["integrated"], abs=1.0)

    def test_zone_target(self):
        calc = EBUR128Calculator()
        # Create signal at ~-23 LUFS equivalent
        sr = 48000
        t = np.linspace(0, 3, sr * 3, endpoint=False)
        amplitude = 10 ** (-23 / 20)
        mono = amplitude * np.sin(2 * np.pi * 1000 * t)
        samples = np.stack([mono, mono]).astype(np.float32)
        
        result = calc.process(samples)
        # After 3 seconds we should have enough blocks
        assert result["zone"] in ("target", "safe")

    def test_reset(self, sine_1khz):
        calc = EBUR128Calculator()
        calc.process(sine_1khz)
        calc.reset()
        result = calc.to_dict()
        assert result["momentary"] == -70.0
        assert result["short_term"] == -70.0
        assert result["integrated"] == -70.0
