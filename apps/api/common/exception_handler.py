"""Turns every API error into {"error": {"code", "message", "details"}}."""
from typing import Any

from django.db.models import ProtectedError
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_handler

from .exceptions import DomainError


def build_envelope(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details if details is not None else {}}}


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DomainError):
        return Response(build_envelope(exc.code, exc.message, exc.details), status=exc.status_code)

    if isinstance(exc, ProtectedError):
        return Response(build_envelope("IN_USE", "Cannot delete: still referenced by orders."), status=409)

    response = drf_default_handler(exc, context)
    if response is None:
        return None  # unexpected error -> Django's 500

    if isinstance(exc, (Http404, drf_exceptions.NotFound)):
        response.data = build_envelope("NOT_FOUND", "Resource not found.")
    elif isinstance(exc, drf_exceptions.ValidationError):
        response.data = build_envelope("VALIDATION_ERROR", "Invalid input.", exc.detail)
    elif isinstance(exc, drf_exceptions.APIException):
        code = str(exc.default_code).upper()
        response.data = build_envelope(code, str(exc.detail))
    return response
