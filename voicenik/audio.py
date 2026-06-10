"""Capture du microphone : 16 kHz mono float32, en mémoire pendant la dictée."""

import logging
import threading

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000


class Recorder:
    def __init__(self, device: int | None = None, max_seconds: int = 120):
        self.device = device
        self.max_seconds = max_seconds
        self._stream: sd.InputStream | None = None
        self._chunks: list[np.ndarray] = []
        self._frames = 0
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self._chunks = []
            self._frames = 0
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            device=self.device,
            callback=self._callback,
        )
        self._stream.start()

    def _callback(self, indata, frames, _time, status) -> None:
        if status:
            logger.warning("Statut audio : %s", status)
        with self._lock:
            if self._frames < self.max_seconds * SAMPLE_RATE:
                self._chunks.append(indata.copy())
                self._frames += frames

    def stop(self) -> np.ndarray:
        """Arrête la capture et renvoie l'audio enregistré (mono float32)."""
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        with self._lock:
            if not self._chunks:
                return np.zeros(0, dtype=np.float32)
            return np.concatenate(self._chunks)[:, 0]


def list_input_devices() -> list[tuple[int, str]]:
    """Liste (index, nom) des périphériques d'entrée disponibles."""
    devices = []
    for idx, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            devices.append((idx, dev["name"]))
    return devices
