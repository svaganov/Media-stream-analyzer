"""Tests for audio analyzer."""
import pytest
import numpy as np

from analyzers.audio.audio_analyzer import AudioAnalyzer, AudioAnalysis


class TestAudioAnalyzer:
    """Test audio analyzer."""

    @pytest.fixture
    def analyzer(self):
        return AudioAnalyzer(sample_rate=48000, channels=2)

    def test_init(self, analyzer):
        assert analyzer.sample_rate == 48000
        assert analyzer.channels == 2

    def test_process_silence(self, analyzer):
        # Silent audio (all zeros)
        samples = np.zeros((2, 48000), dtype=np.float32)
        result = analyzer.process(samples, 0.0)

        assert isinstance(result, AudioAnalysis)
        assert result.dbfs_left <= -60.0  # Should be very low
        assert result.dbfs_right <= -60.0

    def test_process_full_scale(self, analyzer):
        # Full scale sine wave
        t = np.linspace(0, 1, 48000, dtype=np.float32)
        samples = np.array([
            np.sin(2 * np.pi * 1000 * t),
            np.sin(2 * np.pi * 1000 * t)
        ], dtype=np.float32)

        result = analyzer.process(samples, 0.0)

        assert result.dbfs_peak > -10.0  # Should be close to 0 dBFS

    def test_dbfs_calculation(self, analyzer):
        # Known amplitude: 0.5 = -6.02 dBFS
        samples = np.full((2, 4800), 0.5, dtype=np.float32)
        result = analyzer.process(samples, 0.0)

        # Should be approximately -6 dBFS
        assert -10.0 < result.dbfs_peak < -3.0

    def test_reset(self, analyzer):
        samples = np.random.randn(2, 48000).astype(np.float32) * 0.5
        analyzer.process(samples, 0.0)
        analyzer.reset()

        assert analyzer._dbfs_peak_hold == -70.0
        assert len(analyzer._loudness_blocks) == 0

    def test_callbacks(self, analyzer):
        callback = Mock()
        analyzer.on_analysis(callback)

        samples = np.random.randn(2, 48000).astype(np.float32) * 0.1
        analyzer.process(samples, 0.0)

        callback.assert_called_once()


class TestAudioAnalysis:
    """Test audio analysis data class."""

    def test_to_dict(self):
        analysis = AudioAnalysis(
            timestamp=0.0,
            dbfs_left=-12.0,
            dbfs_right=-11.5,
            lufs_m=-23.0,
            lufs_s=-23.0,
            lufs_i=-24.0,
            true_peak=-14.0,
            lra=9.0
        )

        data = analysis.to_dict()
        assert data["dbfs"]["left"] == -12.0
        assert data["lufs"]["m"] == -23.0
        assert data["lra"] == 9.0
