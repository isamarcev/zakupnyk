"""Unit tests for LocalFileStorage.reveal_folder (OS file manager integration)."""

from __future__ import annotations

from pathlib import Path

import pytest

from procflow.domain.exceptions import StorageError
from procflow.infrastructure import file_storage
from procflow.infrastructure.file_storage import LocalFileStorage


@pytest.fixture()
def opened(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Capture Popen calls instead of spawning real processes."""
    calls: list[list[str]] = []
    monkeypatch.setattr(file_storage.shutil, "which", lambda _name: "/usr/bin/open")
    monkeypatch.setattr(file_storage.subprocess, "Popen", lambda args: calls.append(args))
    return calls


def test_reveal_opens_procurement_subfolder(tmp_path: Path, opened: list[list[str]]) -> None:
    (tmp_path / "Закупівля").mkdir()
    LocalFileStorage(root=tmp_path).reveal_folder("Закупівля")
    assert opened == [["/usr/bin/open", str(tmp_path / "Закупівля")]]


def test_reveal_falls_back_to_root_when_no_subfolder(
    tmp_path: Path, opened: list[list[str]]
) -> None:
    LocalFileStorage(root=tmp_path).reveal_folder("Ще не існує")
    assert opened == [["/usr/bin/open", str(tmp_path)]]


def test_reveal_without_file_manager_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(file_storage.shutil, "which", lambda _name: None)
    with pytest.raises(StorageError):
        LocalFileStorage(root=tmp_path).reveal_folder()
