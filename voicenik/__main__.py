"""Point d'entrée : python -m voicenik (ou VoiceNik.exe une fois packagé)."""

import ctypes
import logging
import logging.handlers
import sys

ERROR_ALREADY_EXISTS = 183


def _already_running() -> bool:
    """Mutex Windows nommé : empêche deux instances de se disputer le raccourci."""
    ctypes.windll.kernel32.CreateMutexW(None, False, "VoiceNik_SingleInstance")
    return ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS


def _setup_logging() -> None:
    from voicenik.config import app_data_dir

    handlers: list[logging.Handler] = [
        logging.handlers.RotatingFileHandler(
            app_data_dir() / "voicenik.log",
            maxBytes=512_000,
            backupCount=1,
            encoding="utf-8",
        )
    ]
    if sys.stderr is not None:  # absent en mode fenêtré (pythonw / exe)
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> None:
    _setup_logging()
    if _already_running():
        logging.getLogger(__name__).info("VoiceNik est déjà en cours d'exécution")
        return
    from voicenik.app import VoiceNikApp

    VoiceNikApp().run()


if __name__ == "__main__":
    main()
