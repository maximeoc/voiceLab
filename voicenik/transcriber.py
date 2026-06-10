"""Transcription locale via faster-whisper, avec préchargement en arrière-plan."""

import logging
import os
import threading
from pathlib import Path

from . import config
from .audio import SAMPLE_RATE

logger = logging.getLogger(__name__)

# En dessous de cette durée, l'audio est ignoré (appui accidentel).
MIN_AUDIO_SECONDS = 0.3


def _add_nvidia_dll_dirs() -> None:
    """Rend visibles les DLL cuBLAS/cuDNN installées via pip (wheels nvidia-*)."""
    import site

    bases = []
    try:
        bases += site.getsitepackages()
        bases.append(site.getusersitepackages())
    except Exception:
        pass
    for base in bases:
        nvidia = Path(base) / "nvidia"
        if not nvidia.is_dir():
            continue
        for bin_dir in nvidia.glob("*/bin"):
            try:
                os.add_dll_directory(str(bin_dir))
                os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
            except OSError:
                pass


class Transcriber:
    def __init__(self, settings: config.Settings):
        self.settings = settings
        self._model = None
        self._loaded = threading.Event()
        self._lock = threading.Lock()
        self.status = "non chargé"

    def preload(self) -> None:
        """Charge le modèle dans un thread pour ne pas bloquer le démarrage."""
        threading.Thread(target=self._load, daemon=True, name="model-loader").start()

    def reconfigure(self, settings: config.Settings) -> None:
        with self._lock:
            self.settings = settings
            self._model = None
            self._loaded.clear()
        self.preload()

    def _resolve_device(self) -> str:
        if self.settings.device != "auto":
            return self.settings.device
        try:
            import ctranslate2

            return "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
        except Exception:
            return "cpu"

    def _load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            self.status = "chargement…"
            _add_nvidia_dll_dirs()
            from faster_whisper import WhisperModel

            device = self._resolve_device()
            compute = "float16" if device == "cuda" else "int8"
            download_root = str(config.app_data_dir() / "models")
            try:
                self._model = WhisperModel(
                    self.settings.model,
                    device=device,
                    compute_type=compute,
                    download_root=download_root,
                )
            except Exception:
                if device != "cuda":
                    self.status = "erreur de chargement"
                    logger.exception("Impossible de charger le modèle %s", self.settings.model)
                    return
                logger.exception("Échec CUDA, repli sur CPU int8")
                try:
                    self._model = WhisperModel(
                        self.settings.model,
                        device="cpu",
                        compute_type="int8",
                        download_root=download_root,
                    )
                    device = "cpu"
                except Exception:
                    self.status = "erreur de chargement"
                    logger.exception("Impossible de charger le modèle %s", self.settings.model)
                    return
            self.status = f"{self.settings.model} ({device})"
            self._loaded.set()
            logger.info("Modèle prêt : %s", self.status)

    def _initial_prompt(self) -> str:
        vocab = ", ".join(self.settings.vocabulary)
        return (
            "Dictée en français sur l'informatique et le développement logiciel, "
            f"avec ponctuation. Termes fréquents : {vocab}."
        )

    def transcribe(self, audio) -> str:
        """Transcrit un tableau numpy float32 mono 16 kHz. Bloque si le modèle charge encore."""
        if len(audio) < MIN_AUDIO_SECONDS * SAMPLE_RATE:
            return ""
        if not self._loaded.wait(timeout=300):
            raise RuntimeError(f"Modèle indisponible ({self.status})")
        language = None if self.settings.language == "auto" else self.settings.language
        segments, _info = self._model.transcribe(
            audio,
            language=language,
            initial_prompt=self._initial_prompt(),
            beam_size=5,
            vad_filter=True,
        )
        return "".join(segment.text for segment in segments).strip()
