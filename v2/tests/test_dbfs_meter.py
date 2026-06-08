"""Tests for DBFS Meter — Sprint 1."""

import numpy as np
import pytest
from v2.src.analyzers.audio.dbfs_meter import DBFSMeter


class TestDBFSMeter:
    """Test DBFS peak meter."""

    def test_silence(self, silence):
        meter = DBFSMeter()
        result = meter.process(silence)
        assert result["left"] == -70.0
        assert result["right"] == -70.0
        assert result["peak"] == -70.0
        assert result["zone"] == "silence"

    def test_sine_wave(self, sine_1khz):
        meter = DBFSMeter()
        result = meter.process(sine_1khz)
        # -20 dBFS sine wave should peak around -20 dBFS
        assert -25.0 < result["peak"] < -15.0
        assert result["zone"] == "safe"

    def test_full_scale(self, full_scale):
        meter = DBFSMeter()
        result = meter.process(full_scale)
        # Full-scale sine should peak near 0 dBFS
        assert -3.0 < result["peak"] <= 0.0
        assert result["zone"] == "danger"

    def test_peak_hold(self, full_scale):
        meter = DBFSMeter(hold_time_sec=0.5)
        
        # Process full scale
        result = meter.process(full_scale)
        assert result["peak_hold"] == result["peak"]
        
        # Process silence — hold should persist
        silence = np.zeros((2, 48000), dtype=np.float32)
        result2 = meter.process(silence)
        assert result2["peak_hold"] == pytest.approx(result["peak"], abs=0.1)
        assert result2["peak"] == -70.0

    def test_mono_input(self, sine_1khz):
        meter = DBFSMeter()
        mono = sine_1khz[0]  # Take left channel only
        result = meter.process(mono)
        assert result["left"] == result["right"]  # Mono duplicates to both

    def test_reset(self, full_scale):
        meter = DBFSMeter()
        meter.process(full_scale)
        meter.reset()
        result = meter.to_dict()
        assert result["peak_hold"] == -70.0
