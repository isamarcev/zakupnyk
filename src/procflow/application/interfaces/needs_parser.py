"""Interface for the Excel needs-list parser (implemented in infrastructure)."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from procflow.application.dto import ImportedSheet


class NeedsParser(Protocol):
    def __call__(self, path: Path) -> list[ImportedSheet]:
        """Parse a workbook into import DTOs; raise XlsxImportError on failure."""
        ...
