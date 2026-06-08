"""Tests for Audio Analyzer Orchestrator — Sprint 1."""

import numpy as np
import pytest
from v2.src.analyzers.audio.audio_analyzer import AudioAnalyzer
from v2.src.core.models import AudioAnalysisResult


class TestAudioAnalyzer:
    """Test main audio analyzer orchestrator."""

    def test_init(self):
        analyzer = AudioAnalyzer()
        assert analyzer.sample_rate == 48000
        assert analyzer.channels == 2
        result = analyzer.to_dict()
        assert result["dbfs"]["peak"] == -70.0

    def test_process_silence(self, silence):
        analyzer = AudioAnalyzer()
        result = analyzer.process(silence)
        assert isinstance(result, AudioAnalysisResult)
        assert result.dbfs.peak == -70.0
        assert result.lufs.momentary == -70.0
        assert result.silence.active is True

    def test_process_sine(self, sine_1khz):
        analyzer = AudioAnalyzer()
        result = analyzer.process(sine_1khz)
        assert isinstance(result, AudioAnalysisResult)
        assert -30.0 < result.dbfs.peak < -10.0
        assert result.spectrum.peak_freq_hz > 0
        assert result.silence.active is False

    def test_loudness_history(self, sine_1khz):
        analyzer = AudioAnalyzer()
        # Process multiple seconds to fill history
        for _ in range(5):
            result = analyzer.process(sine_1khz)
        
        history = analyzer.get_history()
        assert len(history) > 0
        assert len(history) <= 60  # Max window

    def test_callback(self, sine_1khz):
        analyzer = AudioAnalyzer()
        callbacks = []
        
        def capture(result):
            callbacks.append(result)
        
        analyzer.on_analysis(capture)
        analyzer.process(sine_1khz)
        
        assert len(callbacks) == 1
        assert isinstance(callbacks[0], AudioAnalysisResult)

    def test_multiple_callbacks(self, sine_1khz):
        analyzer = AudioAnalyzer()
        count = [0, 0]
        
        def cb1(_):
            count[0] += 1
        
        def cb2(_):
            count[1] += 1
        
        analyzer.on_analysis(cb1)
        analyzer.on_analysis(cb2)
        analyzer.process(sine_1khz)
        
        assert count[0] == 1
        assert count[1] == 1

    def test_reset(self, sine_1khz):
        analyzer = AudioAnalyzer()
        analyzer.process(sine_1khz)
        analyzer.reset()
        
        result = analyzer.to_dict()
        assert result["dbfs"]["peak_hold"] == -70.0
        assert len(analyzer.get_history()) == 0

    def test_lra_calculation(self, sine_1khz):
        analyzer = AudioAnalyzer()
        # Process enough data for LRA
        for _ in range(10):
            analyzer.process(sine_1khz)
        
        result = analyzer.process(sine_1khz)
        # LRA should be small for steady sine wave
        assert result.lra >= 0.0
        assert result.lra < 5.0  # Steady signal has small range

    def test_to_dict_serialization(self, sine_1khz):
        analyzer = AudioAnalyzer()
        result = analyzer.process(sine_1khz)
        d = result.to_dict()
        
        assert "timestamp" in d
        assert "dbfs" in d
        assert "lufs" in d
        assert "true_peak" in d
        assert "spectrum" in d
        assert "silence" in d
        assert "loudness_history" in d
        assert "lra" in d
