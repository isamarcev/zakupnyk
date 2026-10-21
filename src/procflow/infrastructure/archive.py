"""Zip packing for document exports."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Callable
from pathlib import Path

from procflow.application.dto import ExportBundle
from procflow.application.interactors.queries.export_documents import LISTING_NAME
from procflow.domain.exceptions import StorageError


def build_zip(bundle: ExportBundle, resolve: Callable[[str], Path]) -> bytes:
    """Скласти архів у памʼяті: перелік + файли документів.

    why: архіви тут — десятки файлів на кілька мегабайт, тож тимчасовий файл на
    диску не потрібен, а віддавати одним шматком простіше й надійніше.
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(LISTING_NAME, bundle.listing)
        for entry in bundle.entries:
            try:
                archive.write(resolve(entry.file_path), entry.arcname)
            except (StorageError, OSError):
                # why: файл могли прибрати з data/files повз застосунок — краще
                # віддати архів із поміткою, ніж впасти на всьому експорті.
                archive.writestr(f"{entry.arcname}.ВІДСУТНІЙ.txt", "Файл не знайдено у сховищі")
    return buffer.getvalue()
