from __future__ import annotations

from fastapi import FastAPI

from genesis.api.routes import artifacts, projects, runs, uploads
from genesis.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="Genesis MVP API", version="0.1.0")
    app.include_router(projects.router)
    app.include_router(uploads.router)
    app.include_router(runs.router)
    app.include_router(artifacts.router)
    return app


app = create_app()
