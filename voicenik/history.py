"""Historique des dernières dictées (50 max), persisté en JSON."""

import json
import logging
from datetime import datetime
from pathlib import Path

from . import config

logger = logging.getLogger(__name__)

MAX_ENTRIES = 50


class History:
    def __init__(self, path: Path | None = None, max_entries: int = MAX_ENTRIES):
        self.path = path or (config.app_data_dir() / "history.json")
        self.max_entries = max_entries
        self._entries = self._load()

    def _load(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except FileNotFoundError:
            return []
        except Exception:
            logger.exception("Historique illisible (%s)", self.path)
            return []

    def add(self, text: str) -> None:
        self._entries.insert(0, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "text": text,
        })
        del self._entries[self.max_entries:]
        self._save()

    def entries(self) -> list[dict]:
        """Dictées de la plus récente à la plus ancienne."""
        return list(self._entries)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
