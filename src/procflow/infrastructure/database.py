"""SQLAlchemy ORM models and engine/session helpers (SQLite)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


class ProcurementRow(Base):
    __tablename__ = "procurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    items: Mapped[list[LineItemRow]] = relationship(
        back_populates="procurement", cascade="all, delete-orphan"
    )
    documents: Mapped[list[DocumentRow]] = relationship(
        back_populates="procurement", cascade="all, delete-orphan"
    )


class LineItemRow(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    procurement_id: Mapped[int] = mapped_column(
        ForeignKey("procurements.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    specification: Mapped[str] = mapped_column(Text, default="")
    qty_required: Mapped[float] = mapped_column(Float, default=0.0)
    qty_ordered: Mapped[float] = mapped_column(Float, default=0.0)
    qty_in_progress: Mapped[float] = mapped_column(Float, default=0.0)
    unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    stage: Mapped[str] = mapped_column(String(20), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    procurement: Mapped[ProcurementRow] = relationship(back_populates="items")
    offers: Mapped[list[OfferRow]] = relationship(
        back_populates="line_item", cascade="all, delete-orphan"
    )


class MessageRow(Base):
    __tablename__ = "item_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    line_item_id: Mapped[int] = mapped_column(
        ForeignKey("line_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class SupplierRow(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    contacts: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    offers: Mapped[list[OfferRow]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class OfferRow(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    line_item_id: Mapped[int] = mapped_column(
        ForeignKey("line_items.id", ondelete="CASCADE"), index=True, nullable=False
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="CASCADE"), index=True, nullable=False
    )
    url: Mapped[str] = mapped_column(Text, default="")
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    line_item: Mapped[LineItemRow] = relationship(back_populates="offers")
    supplier: Mapped[SupplierRow] = relationship(back_populates="offers")


class PayerRow(Base):
    __tablename__ = "payers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    requisites: Mapped[str] = mapped_column(Text, default="")
    iban: Mapped[str] = mapped_column(String(40), default="")
    tax_id: Mapped[str] = mapped_column(String(20), default="")
    bank: Mapped[str] = mapped_column(String(300), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RecipientRow(Base):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(120), default="")
    phone: Mapped[str] = mapped_column(String(60), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    block: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class DocumentRow(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    procurement_id: Mapped[int] = mapped_column(
        ForeignKey("procurements.id", ondelete="CASCADE"), index=True, nullable=False
    )
    supplier_id: Mapped[int | None] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    payer_id: Mapped[int | None] = mapped_column(
        ForeignKey("payers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    original_name: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    doc_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    procurement: Mapped[ProcurementRow] = relationship(back_populates="documents")
    supplier: Mapped[SupplierRow | None] = relationship()
    item_links: Mapped[list[DocumentItemLinkRow]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentItemLinkRow(Base):
    __tablename__ = "document_item_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    line_item_id: Mapped[int] = mapped_column(
        ForeignKey("line_items.id", ondelete="CASCADE"), index=True, nullable=False
    )

    document: Mapped[DocumentRow] = relationship(back_populates="item_links")


def make_engine(db_path: Path) -> Engine:
    """Create a SQLite engine with foreign keys enabled and ensure the schema."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    _ensure_added_columns(engine)
    return engine


def _ensure_added_columns(engine: Engine) -> None:
    """Add columns introduced after the first release to existing databases.

    why: v1 живёт без Alembic; create_all не добавляет колонки в существующие
    таблицы, поэтому новые колонки докатываем точечно и идемпотентно.
    """
    added_columns: list[tuple[str, str, str]] = [
        ("payers", "requisites", "TEXT NOT NULL DEFAULT ''"),
        ("line_items", "stage", "VARCHAR(20) NOT NULL DEFAULT 'new'"),
    ]
    with engine.begin() as connection:
        for table, column, ddl_type in added_columns:
            existing = {row[1] for row in connection.execute(text(f"PRAGMA table_info({table})"))}
            if column not in existing:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}"))


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Session factory bound to the given engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)
