"""Validation hors-ligne du moteur : charge le modèle et transcrit un fichier WAV.

Usage : python scripts/validate.py chemin/vers/echantillon.wav
"""

import sys
import time
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voicenik import postprocess
from voicenik.config import load_settings
from voicenik.transcriber import Transcriber


def load_wav_16k_mono(path: str) -> np.ndarray:
    with wave.open(path, "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        assert wav.getsampwidth() == 2, "WAV 16 bits attendu"
        data = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    audio = data.astype(np.float32) / 32768.0
    if channels > 1:
        audio = audio.reshape(-1, channels).mean(axis=1)
    if rate != 16000:  # rééchantillonnage naïf, suffisant pour la validation
        indices = np.round(np.arange(0, len(audio), rate / 16000)).astype(int)
        audio = audio[indices[indices < len(audio)]]
    return audio


def main() -> None:
    audio = load_wav_16k_mono(sys.argv[1])
    print(f"Audio : {len(audio) / 16000:.1f} s")

    settings = load_settings()
    transcriber = Transcriber(settings)
    started = time.perf_counter()
    transcriber._load()
    print(f"Modèle chargé en {time.perf_counter() - started:.1f} s — {transcriber.status}")

    started = time.perf_counter()
    text = postprocess.apply(transcriber.transcribe(audio))
    elapsed = time.perf_counter() - started
    print(f"Transcription en {elapsed:.2f} s")
    print("---")
    print(text)


if __name__ == "__main__":
    main()
