"""Fenêtre principale : paramètres, test de dictée et historique."""

import dataclasses
import threading
import time
import tkinter as tk
from tkinter import ttk

import pyperclip

from .. import autostart, postprocess
from ..audio import Recorder, list_input_devices

MODELS = ["large-v3-turbo", "medium", "small", "base"]
LANGUAGES = ["fr", "en", "auto"]
DEVICES = ["auto", "cuda", "cpu"]
DEFAULT_MIC_LABEL = "Par défaut (Windows)"
TEST_SECONDS = 4


class SettingsWindow(tk.Toplevel):
    def __init__(self, master: tk.Tk, app):
        super().__init__(master)
        self.app = app
        self.title("VoiceNik — Paramètres")
        self.resizable(False, False)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        self._build_settings_tab(notebook)
        self._build_history_tab(notebook)

        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, foreground="#555").pack(
            anchor="w", padx=12, pady=(0, 8)
        )
        self._refresh_status()

    # ------------------------------------------------------------------ état
    def _refresh_status(self) -> None:
        if not self.winfo_exists():
            return
        self.status_var.set(f"Modèle : {self.app.transcriber.status}")
        self.after(1000, self._refresh_status)

    # ------------------------------------------------------- onglet réglages
    def _build_settings_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="Paramètres")
        settings = self.app.settings
        row = 0

        def label(text: str) -> None:
            ttk.Label(frame, text=text).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))

        # Microphone
        self._mic_choices: list[int | None] = [None]
        mic_labels = [DEFAULT_MIC_LABEL]
        for idx, name in list_input_devices():
            self._mic_choices.append(idx)
            mic_labels.append(f"{idx} — {name}")
        label("Microphone")
        self.mic_var = tk.StringVar(value=DEFAULT_MIC_LABEL)
        if settings.input_device in self._mic_choices:
            self.mic_var.set(mic_labels[self._mic_choices.index(settings.input_device)])
        ttk.Combobox(frame, textvariable=self.mic_var, values=mic_labels,
                     state="readonly", width=42).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        label("Modèle STT")
        self.model_var = tk.StringVar(value=settings.model)
        ttk.Combobox(frame, textvariable=self.model_var, values=MODELS,
                     state="readonly", width=20).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        label("Langue")
        self.language_var = tk.StringVar(value=settings.language)
        ttk.Combobox(frame, textvariable=self.language_var, values=LANGUAGES,
                     state="readonly", width=20).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        label("Matériel")
        self.device_var = tk.StringVar(value=settings.device)
        ttk.Combobox(frame, textvariable=self.device_var, values=DEVICES,
                     state="readonly", width=20).grid(row=row, column=1, sticky="w", pady=3)
        row += 1

        label("Raccourci clavier")
        self.hotkey_var = tk.StringVar(value=settings.hotkey)
        ttk.Entry(frame, textvariable=self.hotkey_var, width=22).grid(
            row=row, column=1, sticky="w", pady=3)
        row += 1

        label("Mode d'écoute")
        self.mode_var = tk.StringVar(value=settings.mode)
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=row, column=1, sticky="w", pady=3)
        ttk.Radiobutton(mode_frame, text="Push-to-talk (maintenir)",
                        variable=self.mode_var, value="push_to_talk").pack(side="left")
        ttk.Radiobutton(mode_frame, text="Toggle (appui / appui)",
                        variable=self.mode_var, value="toggle").pack(side="left", padx=(12, 0))
        row += 1

        label("Insertion du texte")
        self.injection_var = tk.StringVar(value=settings.injection)
        inj_frame = ttk.Frame(frame)
        inj_frame.grid(row=row, column=1, sticky="w", pady=3)
        ttk.Radiobutton(inj_frame, text="Collage (Ctrl+V)",
                        variable=self.injection_var, value="paste").pack(side="left")
        ttk.Radiobutton(inj_frame, text="Frappe simulée",
                        variable=self.injection_var, value="type").pack(side="left", padx=(12, 0))
        row += 1

        self.sounds_var = tk.BooleanVar(value=settings.sounds)
        ttk.Checkbutton(frame, text="Bips de début / fin d'enregistrement",
                        variable=self.sounds_var).grid(row=row, column=1, sticky="w", pady=2)
        row += 1
        self.clipboard_var = tk.BooleanVar(value=settings.restore_clipboard)
        ttk.Checkbutton(frame, text="Restaurer le presse-papiers après l'injection",
                        variable=self.clipboard_var).grid(row=row, column=1, sticky="w", pady=2)
        row += 1
        self.autostart_var = tk.BooleanVar(value=autostart.is_enabled())
        ttk.Checkbutton(frame, text="Lancer VoiceNik au démarrage de Windows",
                        variable=self.autostart_var).grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        label("Vocabulaire technique")
        self.vocab_text = tk.Text(frame, width=44, height=4, font=("Segoe UI", 9))
        self.vocab_text.grid(row=row, column=1, sticky="w", pady=3)
        self.vocab_text.insert("1.0", "\n".join(settings.vocabulary))
        row += 1

        # Test + sauvegarde
        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.test_button = ttk.Button(buttons, text="🎤 Tester la dictée", command=self._on_test)
        self.test_button.pack(side="left")
        ttk.Button(buttons, text="Enregistrer", command=self._on_save).pack(side="left", padx=(10, 0))
        row += 1

        self.test_result = ttk.Label(frame, text="", wraplength=420, foreground="#1a5276")
        self.test_result.grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))

    def _on_test(self) -> None:
        """Enregistre quelques secondes et affiche la transcription, sans injection."""
        if self.app.state != "idle":
            return
        self.test_button.config(state="disabled")
        self.test_result.config(text=f"Parlez maintenant ({TEST_SECONDS} secondes)…")
        threading.Thread(target=self._run_test, daemon=True).start()

    def _run_test(self) -> None:
        try:
            recorder = Recorder(device=self.app.settings.input_device)
            recorder.start()
            time.sleep(TEST_SECONDS)
            audio = recorder.stop()
            started = time.perf_counter()
            text = postprocess.apply(self.app.transcriber.transcribe(audio))
            elapsed = time.perf_counter() - started
            result = f"« {text} »  ({elapsed:.2f} s)" if text else "(rien entendu)"
        except Exception as exc:  # micro absent, modèle en erreur…
            result = f"Erreur : {exc}"
        try:
            self.after(0, self._show_test_result, result)
        except RuntimeError:
            pass  # fenêtre fermée pendant le test

    def _show_test_result(self, result: str) -> None:
        if self.winfo_exists():
            self.test_result.config(text=result)
            self.test_button.config(state="normal")

    def _on_save(self) -> None:
        vocabulary = [t.strip() for t in self.vocab_text.get("1.0", "end").splitlines() if t.strip()]
        mic_index = self._mic_choices[0]
        try:
            mic_label = self.mic_var.get()
            if mic_label != DEFAULT_MIC_LABEL:
                mic_index = int(mic_label.split(" — ")[0])
        except ValueError:
            mic_index = None
        new_settings = dataclasses.replace(
            self.app.settings,
            input_device=mic_index,
            model=self.model_var.get(),
            language=self.language_var.get(),
            device=self.device_var.get(),
            hotkey=self.hotkey_var.get().strip() or "ctrl+space",
            mode=self.mode_var.get(),
            injection=self.injection_var.get(),
            sounds=self.sounds_var.get(),
            restore_clipboard=self.clipboard_var.get(),
            vocabulary=vocabulary,
        )
        self.app.apply_settings(new_settings)
        if self.autostart_var.get():
            autostart.enable()
        else:
            autostart.disable()
        self.test_result.config(text="Paramètres enregistrés.")

    # ----------------------------------------------------- onglet historique
    def _build_history_tab(self, notebook: ttk.Notebook) -> None:
        frame = ttk.Frame(notebook, padding=12)
        notebook.add(frame, text="Historique")

        self.history_list = tk.Listbox(frame, width=70, height=16, font=("Segoe UI", 9))
        self.history_list.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.history_list.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.history_list.config(yscrollcommand=scroll.set)
        self.history_list.bind("<Double-Button-1>", lambda _e: self._copy_selected())

        buttons = ttk.Frame(frame)
        buttons.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Button(buttons, text="Copier", command=self._copy_selected).pack(side="left")
        ttk.Button(buttons, text="Actualiser", command=self._refresh_history).pack(
            side="left", padx=(10, 0))
        self.history_hint = ttk.Label(frame, text="", foreground="#555")
        self.history_hint.grid(row=2, column=0, sticky="w", pady=(6, 0))

        self._refresh_history()

    def _refresh_history(self) -> None:
        self._history_entries = self.app.history.entries()
        self.history_list.delete(0, "end")
        for entry in self._history_entries:
            stamp = entry["timestamp"].replace("T", " ")
            preview = entry["text"].replace("\n", " ⏎ ")
            if len(preview) > 80:
                preview = preview[:80] + "…"
            self.history_list.insert("end", f"{stamp}  —  {preview}")
        self.history_hint.config(
            text=f"{len(self._history_entries)} dictée(s). Double-clic pour copier.")

    def _copy_selected(self) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        pyperclip.copy(self._history_entries[selection[0]]["text"])
        self.history_hint.config(text="Texte copié dans le presse-papiers.")
