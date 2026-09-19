"""
FastAPI application export.
uvicorn target: backend.main:app
"""
from .api.routes import app  # noqa: F401

__all__ = ["app"]
