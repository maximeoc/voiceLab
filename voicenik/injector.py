"""Injection du texte transcrit à la position du curseur de l'application active."""

import logging
import time

import keyboard
import pyperclip

logger = logging.getLogger(__name__)

_MODIFIERS = ("ctrl", "shift", "alt", "windows")


def _wait_keys_released(extra_keys: tuple[str, ...], timeout: float = 1.5) -> None:
    """Attend que le raccourci soit physiquement relâché avant d'injecter,
    sinon les touches encore enfoncées (Ctrl…) corrompraient le Ctrl+V simulé."""
    keys = _MODIFIERS + extra_keys
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if not any(keyboard.is_pressed(k) for k in keys):
                return
        except Exception:
            return
        time.sleep(0.02)


def inject(
    text: str,
    method: str = "paste",
    restore_clipboard: bool = True,
    extra_wait_keys: tuple[str, ...] = (),
) -> None:
    if not text:
        return
    _wait_keys_released(extra_wait_keys)

    if method == "type":
        keyboard.write(text, delay=0.005)
        return

    previous = None
    if restore_clipboard:
        try:
            previous = pyperclip.paste()
        except Exception:
            previous = None
    pyperclip.copy(text)
    time.sleep(0.05)
    keyboard.send("ctrl+v")
    if previous is not None:
        # Laisse le temps à l'application cible de lire le presse-papiers.
        time.sleep(0.3)
        try:
            pyperclip.copy(previous)
        except Exception:
            logger.warning("Impossible de restaurer le presse-papiers")
