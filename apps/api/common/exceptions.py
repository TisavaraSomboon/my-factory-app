"""Domain-level errors raised by services and mapped to HTTP by the exception handler."""
from typing import Any

# Codes that mean "the request is fine but the resource is in the wrong state".
CONFLICT_CODES = {"ORDER_LOCKED", "INVALID_STAGE", "ORDER_COMPLETED", "REJECT_NOT_ALLOWED"}


def http_status_for(code: str) -> int:
    """Return 409 for state conflicts, otherwise 400."""
    return 409 if code in CONFLICT_CODES else 400


class DomainError(Exception):
    """A business-rule violation. Services raise this; they never build Responses."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    @property
    def status_code(self) -> int:
        return http_status_for(self.code)
