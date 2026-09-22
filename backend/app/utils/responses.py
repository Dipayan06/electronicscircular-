"""Consistent API response envelope + error type (Phase 0 §20).

Every endpoint returns `{ "success": bool, "data": ..., "message": str }`.
Business/validation problems raise `APIError`, which the global handlers in
main.py turn into the same envelope with an appropriate HTTP status code (NFR-6:
no raw stack traces reach the client).
"""
from typing import Any


def success(data: Any = None, message: str = "OK") -> dict:
    return {"success": True, "data": data, "message": message}


def failure(message: str) -> dict:
    return {"success": False, "message": message}


class APIError(Exception):
    """Raised by the service layer for expected error conditions."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
