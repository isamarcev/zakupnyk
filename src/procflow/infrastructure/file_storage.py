"""Filesystem-backed document storage: data/files/<procurement>/<supplier>/."""

from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from procflow.domain.exceptions import StorageError

_UNNAMED = "_інше"


def _safe_segment(value: str) -> str:
    """Turn an arbitrary name into a safe folder/file segment."""
    value = unicodedata.normalize("NFKC", value).strip()
    value = re.sub(r"[\\/:*?\"<>|\n\r\t]+", "_", value)
    value = re.sub(r"\s+", " ", value)
    return value[:80] or _UNNAMED


@dataclass(slots=True)
class LocalFileStorage:
    """Stores files under ``root`` keeping a human-browsable folder layout."""

    root: Path

    def save(
        self, *, procurement_name: str, supplier_name: str | None, filename: str, content: bytes
    ) -> str:
        folder = Path(_safe_segment(procurement_name)) / _safe_segment(supplier_name or _UNNAMED)
        target_dir = self.root / folder
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            target = self._unique_path(target_dir / _safe_segment(filename))
            target.write_bytes(content)
        except OSError as exc:
            raise StorageError(f"Не вдалося зберегти файл: {exc}") from exc
        return str(target.relative_to(self.root))

    def absolute_path(self, relative_path: str) -> Path:
        path = (self.root / relative_path).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise StorageError("Некоректний шлях до файлу")
        if not path.is_file():
            raise StorageError(f"Файл не знайдено: {relative_path}")
        return path

    def remove(self, relative_path: str) -> None:
        path = self.root / relative_path
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            raise StorageError(f"Не вдалося видалити файл: {exc}") from exc

    def reveal_folder(self, procurement_name: str | None = None) -> None:
        """Open the files folder in Finder/Explorer; falls back to root when no subfolder yet."""
        folder = self.root
        if procurement_name is not None:
            candidate = self.root / _safe_segment(procurement_name)
            if candidate.is_dir():
                folder = candidate
        # why: 'open' — macOS, 'xdg-open' — Linux desktop; inside Docker neither exists
        opener = shutil.which("open") or shutil.which("xdg-open")
        if opener is None:
            raise StorageError(
                "Немає доступу до файлового менеджера (додаток запущено в контейнері?)"
            )
        try:
            folder.mkdir(parents=True, exist_ok=True)
            subprocess.Popen([opener, str(folder)])  # noqa: S603 — фіксований бінарник, не ввід
        except OSError as exc:
            raise StorageError(f"Не вдалося відкрити папку: {exc}") from exc

    @staticmethod
    def _unique_path(candidate: Path) -> Path:
        """Append `` (n)`` before the suffix until the name is free."""
        if not candidate.exists():
            return candidate
        stem, suffix = candidate.stem, candidate.suffix
        for n in range(1, 1000):
            alternative = candidate.with_name(f"{stem} ({n}){suffix}")
            if not alternative.exists():
                return alternative
        raise StorageError("Забагато файлів з однаковою назвою")
