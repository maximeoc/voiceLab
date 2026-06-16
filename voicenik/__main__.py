"""Point d'entrée : python -m voicenik (ou VoiceNik.exe une fois packagé)."""

import ctypes
import logging
import logging.handlers
import sys

ERROR_ALREADY_EXISTS = 183


def _ensure_admin() -> None:
    """Relance avec élévation UAC si le processus n'est pas administrateur.

    Les hooks clavier WH_KEYBOARD_LL ne traversent pas la barrière de
    privilèges : si le terminal cible tourne en admin et VoiceNik non,
    Ctrl+Espace reste invisible pour le hook.
    """
    if ctypes.windll.shell32.IsUserAnAdmin():
        return
    if getattr(sys, "frozen", False):
        # Exe packagé PyInstaller : sys.executable est déjà l'exe à relancer.
        exe = sys.executable
        params = " ".join(f'"{a}"' for a in sys.argv[1:])
    else:
        exe = sys.executable
        params = " ".join(f'"{a}"' for a in sys.argv)
    ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    sys.exit(0 if ret > 32 else 1)


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
    _ensure_admin()
    _setup_logging()
    if _already_running():
        logging.getLogger(__name__).info("VoiceNik est déjà en cours d'exécution")
        return
    from voicenik.app import VoiceNikApp

    VoiceNikApp().run()


if __name__ == "__main__":
    main()
