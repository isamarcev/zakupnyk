"""Application factory and entrypoint."""

from __future__ import annotations

import logging
import threading
import webbrowser

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from procflow.domain.exceptions import DomainError
from procflow.main.config import Settings
from procflow.main.container import Container, build_container
from procflow.presentation.api import (
    documents,
    import_xlsx,
    orders,
    payers,
    procurements,
    recipients,
    suppliers,
)
from procflow.presentation.templating import templates

logger = logging.getLogger("procflow")


def create_app(container: Container) -> FastAPI:
    """Assemble the FastAPI app with routers and error handling."""
    app = FastAPI(title="Zakupnyk", docs_url=None, redoc_url=None)
    app.state.container = container

    app.include_router(procurements.router)
    app.include_router(orders.router)
    app.include_router(suppliers.router)
    app.include_router(payers.router)
    app.include_router(recipients.router)
    app.include_router(documents.router)
    app.include_router(import_xlsx.router)

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> HTMLResponse:
        logger.warning("domain_error code=%s message=%s", exc.code, exc.message)
        return templates.TemplateResponse(
            request,
            "error.html",
            {"message": exc.message, "code": exc.code, "active": ""},
            status_code=exc.status,
        )

    return app


def main() -> None:
    """Run the local web app and open the browser."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = Settings()
    app = create_app(build_container(settings))

    url = f"http://{settings.host}:{settings.port}"
    if settings.open_browser:
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    logger.info("starting url=%s", url)
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
