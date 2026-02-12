"""Persistent store for per-agent custom instructions."""

import json
from pathlib import Path

from src.utils.config import get_config

VALID_AGENT_KEYS = frozenset({
    "orchestrator",
    "project_manager",
    "document_maker",
    "email_drafter",
})


class PromptStore:
    """JSON-backed store for user-defined agent instruction additions.

    Data is stored at ``~/.clinical_research_assistant/agent_prompts.json``
    (or wherever ``get_config().app_data_dir`` points).
    """

    def __init__(self, path: Path | None = None):
        self._path = path or get_config().app_data_dir / "agent_prompts.json"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, agent_key: str) -> str:
        """Return the custom instructions for *agent_key*, or ``""``."""
        data = self._read()
        return data.get(agent_key, "")

    def set(self, agent_key: str, text: str) -> None:
        """Persist custom instructions for *agent_key*."""
        data = self._read()
        if text.strip():
            data[agent_key] = text
        else:
            data.pop(agent_key, None)
        self._write(data)

    def clear(self, agent_key: str) -> None:
        """Remove custom instructions for *agent_key*."""
        data = self._read()
        if agent_key in data:
            del data[agent_key]
            self._write(data)

    def get_all(self) -> dict[str, str]:
        """Return all stored custom instructions."""
        return self._read()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read(self) -> dict[str, str]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _write(self, data: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
