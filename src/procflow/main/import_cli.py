"""CLI: import a needs-list Excel file into the local database.

Usage: PYTHONPATH=src python -m procflow.main.import_cli <шлях до .xlsx>
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from procflow.infrastructure.xlsx_parser import parse_needs_xlsx
from procflow.main.config import Settings
from procflow.main.container import build_container

logger = logging.getLogger("procflow.import")


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if len(argv) != 1:
        logger.error("Вкажіть шлях до .xlsx файлу")
        return 1
    path = Path(argv[0])
    if not path.is_file():
        logger.error("Файл не знайдено: %s", path)
        return 1

    container = build_container(Settings())
    sheets = parse_needs_xlsx(path)
    with container.unit_of_work() as uow:
        created = uow.import_needs(sheets)
    for procurement in created:
        logger.info("Створено закупівлю id=%s name=%s", procurement.id, procurement.name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
