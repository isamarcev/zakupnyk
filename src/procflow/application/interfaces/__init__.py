"""Application interfaces re-exports."""

from procflow.application.interfaces.file_storage import FileStorage
from procflow.application.interfaces.needs_parser import NeedsParser

__all__ = ["FileStorage", "NeedsParser"]
