"""Tests for FFT Spectrum Analyzer — Sprint 1."""

import numpy as np
import pytest
from v2.src.analyzers.audio.fft_spectrum import FFTSpectrumAnalyzer


class TestFFTSpectrumAnalyzer:
    """Test FFT spectrum analyzer."""

    def test_silence(self, silence):
        analyzer = FFTSpectrumAnalyzer()
        result = analyzer.process(silence)
        assert len(result["bands"]) == 31
        assert all(b == -70.0 for b in result["bands"])
        assert result["peak_freq_hz"] == 0

    def test_1khz_peak(self):
        analyzer = FFTSpectrumAnalyzer(sample_rate=48000, fft_size=2048)
        
        # Generate 1kHz sine
        sr = 48000
        duration = 0.1  # 100ms
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        amplitude = 10 ** (-20 / 20)
        mono = amplitude * np.sin(2 * np.pi * 1000 * t)
        stereo = np.stack([mono, mono]).astype(np.float32)
        
        result = analyzer.process(stereo)
        
        # Peak should be near 1kHz
        assert 900 < result["peak_freq_hz"] < 1100
        assert result["peak_db"] > -40.0

    def test_band_count(self, sine_1khz):
        analyzer = FFTSpectrumAnalyzer(n_bands=31)
        result = analyzer.process(sine_1khz)
        assert len(result["bands"]) == 31

    def test_different_fft_sizes(self):
        for fft_size in [256, 512, 1024, 2048]:
            analyzer = FFTSpectrumAnalyzer(fft_size=fft_size)
            result = analyzer.process(np.zeros((2, 48000), dtype=np.float32))
            assert len(result["bands"]) == 31

    def test_mono_input(self):
        analyzer = FFTSpectrumAnalyzer()
        sr = 48000
        t = np.linspace(0, 0.1, int(sr * 0.1), endpoint=False)
        mono = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        result = analyzer.process(mono)
        assert len(result["bands"]) == 31
