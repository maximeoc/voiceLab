"""Configuration de VoiceNik, persistée en JSON dans %APPDATA%\\VoiceNik."""

import dataclasses
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

APP_NAME = "VoiceNik"

DEFAULT_VOCABULARY = [
    "Kubernetes",
    "GitLab",
    "GitHub",
    "Angular",
    "Spring Boot",
    "DevOps",
    "Docker",
    "TypeScript",
    "JavaScript",
    "Python",
    "Java",
    "API REST",
    "backend",
    "frontend",
    "microservices",
    "pipeline CI/CD",
    "pod",
    "déploiement",
    "merge request",
    "commit",
]


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return app_data_dir() / "config.json"


@dataclass
class Settings:
    language: str = "fr"                # code langue Whisper, ou "auto"
    model: str = "large-v3-turbo"       # large-v3-turbo | medium | small | base
    device: str = "auto"                # auto | cuda | cpu
    hotkey: str = "ctrl+space"
    mode: str = "push_to_talk"          # push_to_talk | toggle
    injection: str = "paste"            # paste | type
    input_device: int | None = None     # index sounddevice, None = micro par défaut
    sounds: bool = True
    restore_clipboard: bool = True
    max_recording_seconds: int = 120
    vocabulary: list[str] = field(default_factory=lambda: list(DEFAULT_VOCABULARY))


def load_settings(path: Path | None = None) -> Settings:
    path = path or config_path()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        known = {f.name for f in dataclasses.fields(Settings)}
        return Settings(**{k: v for k, v in raw.items() if k in known})
    except FileNotFoundError:
        return Settings()
    except Exception:
        logger.exception("Configuration illisible (%s), valeurs par défaut utilisées", path)
        return Settings()


def save_settings(settings: Settings, path: Path | None = None) -> None:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dataclasses.asdict(settings), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
