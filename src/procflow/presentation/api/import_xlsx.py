"""Routes for importing a needs-list from Excel."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from procflow.application.uow import UnitOfWork
from procflow.presentation.api.deps import get_uow
from procflow.presentation.templating import templates

router = APIRouter()


@router.get("/import", response_class=HTMLResponse)
def import_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "import.html", {"active": "import"})


@router.post("/import")
async def import_xlsx(file: UploadFile, uow: UnitOfWork = Depends(get_uow)) -> RedirectResponse:
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        sheets = uow.needs_parser(tmp_path)
        created = uow.import_needs(sheets)
    finally:
        tmp_path.unlink(missing_ok=True)
    if len(created) == 1:
        return RedirectResponse(f"/procurements/{created[0].id}", status_code=303)
    return RedirectResponse("/procurements", status_code=303)
