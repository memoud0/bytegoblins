from __future__ import annotations

from typing import Iterable, Mapping


class ValidationError(ValueError):
    """Raised when the incoming request payload is invalid."""


def require_fields(payload: Mapping[str, object], fields: Iterable[str]) -> None:
    missing = [field for field in fields if not payload.get(field)]
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")
