"""FastAPI dependencies shared by routers."""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Request

from procflow.application.uow import UnitOfWork


def get_uow(request: Request) -> Iterator[UnitOfWork]:
    """Per-request unit of work; container is attached to app.state in main."""
    with request.app.state.container.unit_of_work() as uow:
        yield uow
