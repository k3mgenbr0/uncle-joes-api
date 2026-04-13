"""
Uncle Joe's Coffee Company - FastAPI entrypoint

Supports the starter workflow:

    poetry install
    poetry run uvicorn main:app --reload

This file keeps the starter command working while the real application
code lives in the modular `app/` package.
"""

from app.main import app

__all__ = ["app"]
