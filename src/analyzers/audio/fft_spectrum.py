"""
FFT Spectrum Analyzer for Media Stream Analyzer

Real-time 1024-point FFT for audio spectrum analysis.
Frequency range: 0-20kHz (or up to Nyquist = sample_rate/2)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SpectrumData:
    """FFT spectrum data container."""
    frequencies: np.ndarray      # Frequency bins (Hz)
    magnitudes_db: np.ndarray    # Magnitude in dB
    peak_frequency: float       # Peak frequency (Hz)
    peak_magnitude_db: float    # Peak magnitude (dB)
    sample_rate: int            # Sample rate
    fft_size: int               # FFT size (1024)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "frequencies": self.frequencies.tolist(),
            "magnitudes_db": self.magnitudes_db.tolist(),
            "peak_frequency": self.peak_frequency,
            "peak_magnitude_db": self.peak_magnitude_db,
            "sample_rate": self.sample_rate,
            "fft_size": self.fft_size
        }


class FFTSpectrumAnalyzer:
    """
    Real-time FFT spectrum analyzer.

    Uses NumPy's rfft for efficient real-valued FFT.
    Window function: Hann window for reduced spectral leakage.

    Args:
        fft_size: FFT size (default 1024, must be power of 2)
        sample_rate: Audio sample rate (default 48000)
        overlap: Overlap ratio (0.0-1.0, default 0.5 for 50% overlap)
    """

    def __init__(self, fft_size: int = 1024, sample_rate: int = 48000, overlap: float = 0.5):
        if not (fft_size & (fft_size - 1) == 0):  # Check power of 2
            raise ValueError("fft_size must be a power of 2")

        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.overlap = overlap
        self.hop_size = int(fft_size * (1 - overlap))

        # Hann window for spectral leakage reduction
        self.window = np.hanning(fft_size)

        # Frequency bins
        self.freq_bins = np.fft.rfftfreq(fft_size, 1.0 / sample_rate)

        # Buffer for overlapping frames
        self._buffer = np.zeros(0, dtype=np.float32)

        # Smoothing factor for display (0.0-1.0, higher = more smoothing)
        self.smoothing = 0.8
        self._smoothed_spectrum = None

        # Number of display bands (for UI bar graph)
        self.display_bands = 64

    def process(self, pcm_data: np.ndarray) -> Optional[SpectrumData]:
        """
        Process PCM audio data and return spectrum.

        Args:
            pcm_data: PCM audio samples (float32, mono or stereo interleaved)

        Returns:
            SpectrumData or None if not enough data
        """
        # Convert to mono if stereo
        if len(pcm_data.shape) > 1 and pcm_data.shape[1] == 2:
            pcm_data = (pcm_data[:, 0] + pcm_data[:, 1]) / 2.0

        # Append to buffer
        self._buffer = np.concatenate([self._buffer, pcm_data])

        # Check if we have enough data
        if len(self._buffer) < self.fft_size:
            return None

        # Process all available frames
        frames = []
        pos = 0
        while pos + self.fft_size <= len(self._buffer):
            frame = self._buffer[pos:pos + self.fft_size]

            # Apply window
            windowed = frame * self.window

            # FFT
            fft_result = np.fft.rfft(windowed)

            # Magnitude
            magnitude = np.abs(fft_result)

            # Convert to dB (avoid log(0))
            magnitude_db = 20 * np.log10(magnitude + 1e-10)

            frames.append(magnitude_db)
            pos += self.hop_size

        # Keep remaining samples for next call
        self._buffer = self._buffer[pos:]

        if not frames:
            return None

        # Average multiple frames
        avg_spectrum = np.mean(frames, axis=0)

        # Apply smoothing for visual stability
        if self._smoothed_spectrum is None:
            self._smoothed_spectrum = avg_spectrum
        else:
            self._smoothed_spectrum = (
                self.smoothing * self._smoothed_spectrum + 
                (1 - self.smoothing) * avg_spectrum
            )

        # Find peak
        peak_idx = np.argmax(self._smoothed_spectrum)
        peak_freq = self.freq_bins[peak_idx]
        peak_mag = self._smoothed_spectrum[peak_idx]

        return SpectrumData(
            frequencies=self.freq_bins.copy(),
            magnitudes_db=self._smoothed_spectrum.copy(),
            peak_frequency=float(peak_freq),
            peak_magnitude_db=float(peak_mag),
            sample_rate=self.sample_rate,
            fft_size=self.fft_size
        )

    def get_display_bands(self, spectrum: SpectrumData, 
                         band_count: int = 64,
                         scale: str = "log") -> Dict:
        """
        Convert full spectrum to display bands for UI bar graph.

        Args:
            spectrum: SpectrumData from process()
            band_count: Number of bands (default 64)
            scale: "log" or "linear" frequency scale

        Returns:
            Dict with band frequencies and magnitudes
        """
        freqs = spectrum.frequencies
        mags = spectrum.magnitudes_db

        if scale == "log":
            # Logarithmic frequency bands
            min_freq = 20  # 20 Hz
            max_freq = min(self.sample_rate / 2, 20000)

            log_min = np.log10(min_freq)
            log_max = np.log10(max_freq)
            log_bands = np.linspace(log_min, log_max, band_count + 1)
            band_edges = 10 ** log_bands
        else:
            # Linear frequency bands
            band_edges = np.linspace(0, self.sample_rate / 2, band_count + 1)

        band_mags = []
        band_centers = []

        for i in range(band_count):
            low = band_edges[i]
            high = band_edges[i + 1]

            # Find indices in this band
            mask = (freqs >= low) & (freqs < high)
            if np.any(mask):
                band_mag = float(np.mean(mags[mask]))
            else:
                band_mag = -99.0  # Silence

            band_mags.append(band_mag)
            band_centers.append(float((low + high) / 2))

        return {
            "bands": band_count,
            "frequencies": band_centers,
            "magnitudes_db": band_mags,
            "scale": scale,
            "peak_frequency": spectrum.peak_frequency,
            "peak_magnitude_db": spectrum.peak_magnitude_db
        }

    def reset(self) -> None:
        """Reset internal state."""
        self._buffer = np.zeros(0, dtype=np.float32)
        self._smoothed_spectrum = None

    @property
    def nyquist(self) -> float:
        """Nyquist frequency (half sample rate)."""
        return self.sample_rate / 2.0


class SpectrumHistory:
    """
    History buffer for spectrum data over time.
    Used for waterfall/spectrogram display.
    """

    def __init__(self, max_frames: int = 300):
        self.max_frames = max_frames
        self._history: List[SpectrumData] = []

    def add(self, spectrum: SpectrumData) -> None:
        """Add spectrum frame to history."""
        self._history.append(spectrum)
        if len(self._history) > self.max_frames:
            self._history.pop(0)

    def get_waterfall_data(self, band_count: int = 64) -> List[Dict]:
        """
        Get data for waterfall/spectrogram display.

        Returns:
            List of {timestamp, bands: [magnitudes]} dicts
        """
        result = []
        for spec in self._history:
            bands = FFTSpectrumAnalyzer(fft_size=spec.fft_size, sample_rate=spec.sample_rate)
            display = bands.get_display_bands(spec, band_count=band_count)
            result.append({
                "timestamp": time.time(),
                "magnitudes_db": display["magnitudes_db"]
            })
        return result

    def clear(self) -> None:
        """Clear history."""
        self._history.clear()

    @property
    def frame_count(self) -> int:
        return len(self._history)
