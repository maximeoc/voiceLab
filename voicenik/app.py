"""Orchestrateur : machine à états IDLE → RECORDING → TRANSCRIBING → injection.

Threads en présence :
- thread principal : boucle tkinter (overlay, fenêtre de paramètres) ;
- thread pystray (icône de notification) ;
- thread de la lib `keyboard` (hooks globaux) → appelle start/stop_recording ;
- thread de chargement du modèle, puis threads éphémères de transcription.
Les mises à jour d'UI passent toutes par la file `_events`, dépouillée côté tkinter.
"""

import logging
import queue
import threading
import time
import tkinter as tk
import winsound
from pathlib import Path

import keyboard

from . import injector, postprocess
from .audio import SAMPLE_RATE, Recorder
from .config import Settings, load_settings, save_settings
from .history import History
from .hotkey import HotkeyListener
from .transcriber import MIN_AUDIO_SECONDS, Transcriber
from .ui.overlay import Overlay
from .ui.settings_window import SettingsWindow
from .ui.tray import Tray

logger = logging.getLogger(__name__)

IDLE = "idle"
RECORDING = "recording"
TRANSCRIBING = "transcribing"

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


class VoiceNikApp:
    def __init__(self):
        self.settings = load_settings()
        self.history = History()
        self.transcriber = Transcriber(self.settings)
        self.recorder = Recorder(
            device=self.settings.input_device,
            max_seconds=self.settings.max_recording_seconds,
        )
        self.state = IDLE
        self._state_lock = threading.Lock()
        self._events: queue.Queue = queue.Queue()
        self._listener: HotkeyListener | None = None
        self._settings_window: SettingsWindow | None = None
        self.root: tk.Tk | None = None

    # ------------------------------------------- cycle de dictée (thread clavier)
    def start_recording(self) -> None:
        with self._state_lock:
            if self.state != IDLE:
                return
            self.state = RECORDING
        try:
            self.recorder.start()
        except Exception:
            logger.exception("Impossible de démarrer la capture audio")
            with self._state_lock:
                self.state = IDLE
            return
        self._play_sound("start.wav")
        self._events.put(("state", RECORDING))

    def stop_recording(self) -> None:
        with self._state_lock:
            if self.state != RECORDING:
                return
            self.state = TRANSCRIBING
        audio = self.recorder.stop()
        self._play_sound("stop.wav")
        self._events.put(("state", TRANSCRIBING))
        threading.Thread(target=self._process, args=(audio,), daemon=True).start()

    def _process(self, audio) -> None:
        started = time.perf_counter()
        try:
            text = ""
            if len(audio) >= MIN_AUDIO_SECONDS * SAMPLE_RATE:
                text = postprocess.apply(self.transcriber.transcribe(audio))
            if text:
                injector.inject(
                    text,
                    method=self.settings.injection,
                    restore_clipboard=self.settings.restore_clipboard,
                    extra_wait_keys=tuple(self.settings.hotkey.split("+")),
                )
                self.history.add(text)
            logger.info(
                "Dictée de %.1f s traitée en %.2f s (%d caractères)",
                len(audio) / SAMPLE_RATE, time.perf_counter() - started, len(text),
            )
        except Exception:
            logger.exception("Échec du traitement de la dictée")
        finally:
            with self._state_lock:
                self.state = IDLE
            self._events.put(("state", IDLE))

    def _play_sound(self, filename: str) -> None:
        if self.settings.sounds:
            winsound.PlaySound(
                str(ASSETS_DIR / filename), winsound.SND_FILENAME | winsound.SND_ASYNC
            )

    # ------------------------------------------------------------- paramètres
    def apply_settings(self, new: Settings) -> None:
        old = self.settings
        self.settings = new
        save_settings(new)
        if (new.hotkey, new.mode) != (old.hotkey, old.mode):
            self._restart_listener()
        if (new.input_device, new.max_recording_seconds) != (
            old.input_device, old.max_recording_seconds
        ):
            self.recorder = Recorder(
                device=new.input_device, max_seconds=new.max_recording_seconds
            )
        if (new.model, new.device, new.language, tuple(new.vocabulary)) != (
            old.model, old.device, old.language, tuple(old.vocabulary)
        ):
            self.transcriber.reconfigure(new)
        logger.info("Paramètres mis à jour")

    def _restart_listener(self) -> None:
        if self._listener is not None:
            self._listener.stop()
        self._listener = HotkeyListener(
            self.settings.hotkey,
            self.settings.mode,
            on_start=self.start_recording,
            on_stop=self.stop_recording,
        )
        self._listener.start()

    # --------------------------------------------------------------- boucle UI
    def run(self) -> None:
        logger.info("Démarrage de VoiceNik")
        self.transcriber.preload()
        self._restart_listener()

        self.root = tk.Tk()
        self.root.withdraw()
        self.overlay = Overlay(self.root)
        self.tray = Tray(
            on_open_settings=lambda: self._events.put(("open_settings", None)),
            on_quit=lambda: self._events.put(("quit", None)),
        )
        self.tray.start()
        self.root.after(50, self._poll_events)
        self.root.mainloop()

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "state":
                    self._update_state_ui(payload)
                elif kind == "open_settings":
                    self._open_settings()
                elif kind == "quit":
                    self._quit()
                    return
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    def _update_state_ui(self, state: str) -> None:
        self.tray.set_state(state)
        if state in (RECORDING, TRANSCRIBING):
            self.overlay.show(state)
        else:
            self.overlay.hide()

    def _open_settings(self) -> None:
        if self._settings_window is not None and self._settings_window.winfo_exists():
            self._settings_window.lift()
            self._settings_window.focus_force()
        else:
            self._settings_window = SettingsWindow(self.root, self)

    def _quit(self) -> None:
        logger.info("Arrêt de VoiceNik")
        if self._listener is not None:
            self._listener.stop()
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        self.tray.stop()
        self.root.destroy()
