"""Pastille d'état discrète et animée, centrée en haut de l'écran pendant la dictée."""

import tkinter as tk

_TRANSPARENT = "#ff00ff"
_BG = "#2b2b2e"
_TEXT = "#f2f2f2"
_WIDTH, _HEIGHT, _RADIUS = 200, 46, 16
_MARGIN_TOP = 24

_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_PULSE_RADII = (5, 6, 7, 6)

_STATES = {
    "recording": {"accent": "#ff6b6b", "text": "Écoute…"},
    "transcribing": {"accent": "#f5b041", "text": "Transcription…"},
}


def _rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs):
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class Overlay:
    def __init__(self, root: tk.Tk):
        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.config(bg=_TRANSPARENT)
        self.win.attributes("-transparentcolor", _TRANSPARENT)

        self.canvas = tk.Canvas(
            self.win, width=_WIDTH, height=_HEIGHT, bg=_TRANSPARENT, highlightthickness=0
        )
        self.canvas.pack()

        self._anim_job: str | None = None
        self._fade_job: str | None = None
        self._tick = 0
        self._dot = None
        self._spinner = None

    def show(self, state: str) -> None:
        cfg = _STATES[state]
        self._cancel_job("_anim_job")
        self.canvas.delete("all")
        _rounded_rect(self.canvas, 1, 1, _WIDTH - 1, _HEIGHT - 1, _RADIUS, fill=_BG, outline="")

        if state == "recording":
            self._dot = self.canvas.create_oval(0, 0, 0, 0, fill=cfg["accent"], outline="")
            self._spinner = None
        else:
            self._dot = None
            self._spinner = self.canvas.create_text(
                26, _HEIGHT // 2, text="", fill=cfg["accent"], font=("Segoe UI", 13, "bold")
            )
        self.canvas.create_text(
            _WIDTH // 2 + 12, _HEIGHT // 2, text=cfg["text"],
            fill=_TEXT, font=("Segoe UI", 10), anchor="center",
        )

        self._tick = 0
        self._animate(state)

        self.win.update_idletasks()
        x = (self.win.winfo_screenwidth() - _WIDTH) // 2
        y = _MARGIN_TOP
        self.win.geometry(f"{_WIDTH}x{_HEIGHT}+{x}+{y}")
        self.win.deiconify()
        self._fade_to(0.92)

    def hide(self) -> None:
        self._cancel_job("_anim_job")
        self._fade_to(0.0, then=self.win.withdraw)

    def _animate(self, state: str) -> None:
        if state == "recording":
            radius = _PULSE_RADII[self._tick % len(_PULSE_RADII)]
            cx, cy = 26, _HEIGHT // 2
            self.canvas.coords(self._dot, cx - radius, cy - radius, cx + radius, cy + radius)
            delay = 250
        else:
            frame = _SPINNER_FRAMES[self._tick % len(_SPINNER_FRAMES)]
            self.canvas.itemconfig(self._spinner, text=frame)
            delay = 80
        self._tick += 1
        self._anim_job = self.win.after(delay, self._animate, state)

    def _fade_to(self, target: float, then=None) -> None:
        self._cancel_job("_fade_job")
        current = float(self.win.attributes("-alpha"))
        step = 0.2
        if abs(target - current) <= step:
            self.win.attributes("-alpha", target)
            if then:
                then()
            return
        current += step if target > current else -step
        self.win.attributes("-alpha", current)
        self._fade_job = self.win.after(15, self._fade_to, target, then)

    def _cancel_job(self, attr: str) -> None:
        job = getattr(self, attr)
        if job is not None:
            self.win.after_cancel(job)
            setattr(self, attr, None)
