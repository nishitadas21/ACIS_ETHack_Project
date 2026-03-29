"""
Compatibility shim: run the API via `python -m uvicorn api.app:app --reload`.
"""

from api.app import app

__all__ = ["app"]
