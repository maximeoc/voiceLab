"""Raccourci clavier global : modes push-to-talk (maintien) et toggle (appui/appui)."""

import logging

import keyboard

logger = logging.getLogger(__name__)


class HotkeyListener:
    def __init__(self, hotkey: str, mode: str, on_start, on_stop):
        self.hotkey = hotkey.lower().replace(" ", "")
        self.mode = mode
        self.on_start = on_start
        self.on_stop = on_stop
        self._recording = False
        self._pressed = False  # filtre la répétition automatique de la touche maintenue
        self._hotkey_handle = None
        self._release_handle = None

    @property
    def main_key(self) -> str:
        return self.hotkey.split("+")[-1]

    def start(self) -> None:
        self._hotkey_handle = keyboard.add_hotkey(self.hotkey, self._on_press, suppress=True)
        self._release_handle = keyboard.on_release_key(self.main_key, self._on_release)
        logger.info("Raccourci actif : %s (mode %s)", self.hotkey, self.mode)

    def stop(self) -> None:
        if self._hotkey_handle is not None:
            try:
                keyboard.remove_hotkey(self._hotkey_handle)
            except (KeyError, ValueError):
                pass
            self._hotkey_handle = None
        if self._release_handle is not None:
            try:
                keyboard.unhook(self._release_handle)
            except (KeyError, ValueError):
                pass
            self._release_handle = None

    def _on_press(self) -> None:
        if self._pressed:
            return
        self._pressed = True
        if self.mode == "toggle":
            if self._recording:
                self._recording = False
                self.on_stop()
            else:
                self._recording = True
                self.on_start()
        else:  # push_to_talk
            if not self._recording:
                self._recording = True
                self.on_start()

    def _on_release(self, _event) -> None:
        self._pressed = False
        if self.mode == "push_to_talk" and self._recording:
            self._recording = False
            self.on_stop()
