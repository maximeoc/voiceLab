"""Génère les sons de notification (douces glissades sinusoïdales) de VoiceNik.

Usage : python scripts/generate_sounds.py
"""

import wave
from pathlib import Path

import numpy as np

ASSETS = Path(__file__).resolve().parent.parent / "voicenik" / "assets"
RATE = 44100


def _chirp(freq_start: float, freq_end: float, duration: float, volume: float) -> np.ndarray:
    t = np.arange(int(RATE * duration))
    freq = np.linspace(freq_start, freq_end, len(t))
    samples = np.sin(2 * np.pi * np.cumsum(freq) / RATE)
    fade = int(RATE * 0.012)
    envelope = np.ones_like(samples)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    return (samples * envelope * volume * 32767).astype(np.int16)


def _save(name: str, data: np.ndarray) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    path = ASSETS / name
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(RATE)
        wav_file.writeframes(data.tobytes())
    print(f"écrit {path}")


def main() -> None:
    _save("start.wav", _chirp(520, 760, 0.09, volume=0.22))
    _save("stop.wav", _chirp(640, 460, 0.11, volume=0.20))


if __name__ == "__main__":
    main()
