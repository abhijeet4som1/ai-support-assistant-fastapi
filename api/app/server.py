"""ASGI entry for uvicorn: `uvicorn app.server:app`."""

from app.main import production_app

app = production_app()
