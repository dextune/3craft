"""ASGI entrypoint: uvicorn services.api.main:app."""

from threecraft.api import create_app

app = create_app()

__all__ = ["app"]
