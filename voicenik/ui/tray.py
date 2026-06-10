"""Icône de la zone de notification Windows (pystray)."""

import pystray
from PIL import Image, ImageDraw

STATE_COLORS = {
    "idle": "#4a90d9",
    "recording": "#ff6b6b",
    "transcribing": "#f5b041",
}
STATE_TITLES = {
    "idle": "VoiceNik — prêt",
    "recording": "VoiceNik — enregistrement…",
    "transcribing": "VoiceNik — transcription…",
}


def _make_image(color: str) -> Image.Image:
    """Petit pictogramme micro sur fond rond coloré."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((2, 2, 62, 62), fill=color)
    # corps du micro
    draw.rounded_rectangle((26, 14, 38, 36), radius=6, fill="white")
    # arceau + pied
    draw.arc((20, 22, 44, 44), start=0, end=180, fill="white", width=3)
    draw.line((32, 44, 32, 50), fill="white", width=3)
    draw.line((25, 50, 39, 50), fill="white", width=3)
    return img


class Tray:
    def __init__(self, on_open_settings, on_quit):
        menu = pystray.Menu(
            pystray.MenuItem("Paramètres", lambda icon, item: on_open_settings(), default=True),
            pystray.MenuItem("Quitter", lambda icon, item: on_quit()),
        )
        self.icon = pystray.Icon(
            "VoiceNik",
            _make_image(STATE_COLORS["idle"]),
            STATE_TITLES["idle"],
            menu,
        )

    def start(self) -> None:
        self.icon.run_detached()

    def set_state(self, state: str) -> None:
        self.icon.icon = _make_image(STATE_COLORS.get(state, STATE_COLORS["idle"]))
        self.icon.title = STATE_TITLES.get(state, STATE_TITLES["idle"])

    def stop(self) -> None:
        self.icon.stop()
