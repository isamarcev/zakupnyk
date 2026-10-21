"""Dependency wiring: engine, session factory, per-request unit of work."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from procflow.application.uow import UnitOfWork
from procflow.infrastructure.database import make_engine, make_session_factory
from procflow.infrastructure.file_storage import LocalFileStorage
from procflow.infrastructure.repositories.document_repo import SqlDocumentRepository
from procflow.infrastructure.repositories.message_repo import SqlMessageRepository
from procflow.infrastructure.repositories.offer_repo import SqlOfferRepository
from procflow.infrastructure.repositories.payer_repo import SqlPayerRepository
from procflow.infrastructure.repositories.procurement_repo import (
    SqlLineItemRepository,
    SqlProcurementRepository,
)
from procflow.infrastructure.repositories.recipient_repo import SqlRecipientRepository
from procflow.infrastructure.repositories.stage_change_repo import SqlStageChangeRepository
from procflow.infrastructure.repositories.supplier_order_repo import SqlSupplierOrderRepository
from procflow.infrastructure.repositories.supplier_repo import SqlSupplierRepository
from procflow.infrastructure.xlsx_parser import parse_needs_xlsx
from procflow.main.config import Settings


@dataclass(slots=True)
class Container:
    """Application-scoped container: engine, session factory, storage."""

    settings: Settings
    engine: Engine
    session_factory: sessionmaker[Session]
    storage: LocalFileStorage

    @contextmanager
    def unit_of_work(self) -> Iterator[UnitOfWork]:
        """Open a session, yield a UnitOfWork, commit on success / rollback on error."""
        session = self.session_factory()
        try:
            yield UnitOfWork(
                procurements=SqlProcurementRepository(session),
                items=SqlLineItemRepository(session),
                suppliers=SqlSupplierRepository(session),
                offers=SqlOfferRepository(session),
                documents=SqlDocumentRepository(session),
                payers=SqlPayerRepository(session),
                recipients=SqlRecipientRepository(session),
                messages=SqlMessageRepository(session),
                stage_changes=SqlStageChangeRepository(session),
                orders=SqlSupplierOrderRepository(session),
                storage=self.storage,
                needs_parser=parse_needs_xlsx,
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def build_container(settings: Settings) -> Container:
    """Create engine, ensure schema and folders, wire the container."""
    engine = make_engine(settings.db_path)
    settings.files_dir.mkdir(parents=True, exist_ok=True)
    return Container(
        settings=settings,
        engine=engine,
        session_factory=make_session_factory(engine),
        storage=LocalFileStorage(root=settings.files_dir),
    )
