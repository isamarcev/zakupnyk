"""Commands for payers (funds/persons whose requisites pay the invoices).

The payer can be created from a single pasted requisites block: the name is
taken from the first line and IBAN / ІПН / ЄДРПОУ are extracted automatically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from procflow.application.dto import PayerInput
from procflow.application.interfaces.repositories import PayerRepository
from procflow.domain.entities import Payer
from procflow.domain.exceptions import InvalidInputError

_IBAN_RE = re.compile(r"\bUA\d{27}\b")
# why: ЄДРПОУ — 8 цифр, ІПН — 10; ищем после маркера, чтобы не путать с телефоном/индексом
_TAX_ID_RE = re.compile(r"(?:ЄДРПОУ|ІПН|ЕГРПОУ|ИНН)\D{0,20}?(\d{8,10})", re.IGNORECASE)


def _normalized(data: PayerInput) -> tuple[str, PayerInput]:
    """Derive missing name/iban/tax_id from the pasted requisites block."""
    requisites = data.requisites.strip()
    name = data.name.strip()
    if not name and requisites:
        first_line = next((line.strip() for line in requisites.splitlines() if line.strip()), "")
        name = first_line[:300]
    if not name:
        raise InvalidInputError("Вкажіть отримувача або вставте блок реквізитів")

    iban = data.iban.strip()
    if not iban and requisites:
        match = _IBAN_RE.search(requisites.replace(" ", ""))
        iban = match.group(0) if match else ""

    tax_id = data.tax_id.strip()
    if not tax_id and requisites:
        match = _TAX_ID_RE.search(requisites)
        tax_id = match.group(1) if match else ""

    return name, PayerInput(
        name=name,
        requisites=requisites,
        iban=iban,
        tax_id=tax_id,
        bank=data.bank.strip(),
        notes=data.notes.strip(),
    )


@dataclass(slots=True)
class CreatePayer:
    payers: PayerRepository

    def __call__(self, data: PayerInput) -> Payer:
        name, normalized = _normalized(data)
        return self.payers.add(
            Payer(
                id=None,
                name=name,
                requisites=normalized.requisites,
                iban=normalized.iban,
                tax_id=normalized.tax_id,
                bank=normalized.bank,
                notes=normalized.notes,
            )
        )


@dataclass(slots=True)
class UpdatePayer:
    payers: PayerRepository

    def __call__(self, payer_id: int, data: PayerInput) -> Payer:
        name, normalized = _normalized(data)
        payer = self.payers.get(payer_id)
        payer.name = name
        payer.requisites = normalized.requisites
        payer.iban = normalized.iban
        payer.tax_id = normalized.tax_id
        payer.bank = normalized.bank
        payer.notes = normalized.notes
        self.payers.update(payer)
        return payer


@dataclass(slots=True)
class DeletePayer:
    payers: PayerRepository

    def __call__(self, payer_id: int) -> None:
        self.payers.get(payer_id)  # raises if missing
        self.payers.delete(payer_id)


@dataclass(slots=True)
class ListPayers:
    payers: PayerRepository

    def __call__(self, *, query: str | None = None) -> list[Payer]:
        return self.payers.list_all(query=query)
