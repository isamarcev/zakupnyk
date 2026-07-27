"""Shared fixtures: in-memory-ish container on a tmp dir, FastAPI test client."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from procflow.application.uow import UnitOfWork
from procflow.main.app import create_app
from procflow.main.config import Settings
from procflow.main.container import Container, build_container


@pytest.fixture()
def container(tmp_path: Path) -> Container:
    return build_container(Settings(data_dir=tmp_path / "data"))


@pytest.fixture()
def uow(container: Container) -> Iterator[UnitOfWork]:
    with container.unit_of_work() as unit:
        yield unit


@pytest.fixture()
def client(container: Container) -> TestClient:
    return TestClient(create_app(container))
