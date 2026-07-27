"""File storage interface: managed folder for invoice/document files."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileStorage(Protocol):
    def save(
        self, *, procurement_name: str, supplier_name: str | None, filename: str, content: bytes
    ) -> str:
        """Store content under files/<procurement>/<supplier>/ and return the relative path."""
        ...

    def absolute_path(self, relative_path: str) -> Path:
        """Resolve a stored relative path to an absolute one, raise StorageError if missing."""
        ...

    def remove(self, relative_path: str) -> None:
        """Delete the stored file; missing file is not an error."""
        ...

    def reveal_folder(self, procurement_name: str | None = None) -> None:
        """Open the storage folder (or the procurement's subfolder) in the OS file manager.

        Raises StorageError when no file manager is available (e.g. inside Docker).
        """
        ...
