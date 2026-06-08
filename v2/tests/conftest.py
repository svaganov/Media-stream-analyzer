"""Pytest configuration and fixtures for v2."""

import pytest
import numpy as np


@pytest.fixture
def sample_rate():
    """Default sample rate for tests."""
    return 48000


@pytest.fixture
def silence():
    """Silent audio frame (1 second)."""
    return np.zeros((2, 48000), dtype=np.float32)


@pytest.fixture
def sine_1khz():
    """1kHz sine wave at -20 dBFS (1 second, stereo)."""
    sr = 48000
    t = np.linspace(0, 1, sr, endpoint=False)
    amplitude = 10 ** (-20 / 20)  # -20 dBFS
    mono = amplitude * np.sin(2 * np.pi * 1000 * t)
    return np.stack([mono, mono]).astype(np.float32)


@pytest.fixture
def full_scale():
    """Full-scale sine wave (0 dBFS)."""
    sr = 48000
    t = np.linspace(0, 1, sr, endpoint=False)
    mono = np.sin(2 * np.pi * 1000 * t)
    return np.stack([mono, mono]).astype(np.float32)
