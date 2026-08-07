"""Operational boundary for Suwappu calls made by CrewAI tools.

The shared SDK already applies an HTTP deadline. This layer adds a shorter,
product-controlled deadline, typed transport/protocol failures, and
metadata-only request events without exposing prompts, tool arguments, wallet
addresses, response bodies, or credentials.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import httpx
from pydantic import ValidationError
from suwappu import SuwappuError

_T = TypeVar("_T")
_DEFAULT_OPERATION_TIMEOUT_SECONDS = 25.0
_MAX_OPERATION_TIMEOUT_SECONDS = 30.0
logger = logging.getLogger("suwappu_crewai.api")


class SuwappuRuntimeError(RuntimeError):
    """Base class for adapter-level operational failures."""


class SuwappuTransportError(SuwappuRuntimeError):
    """A request deadline or network transport failed."""

    def __init__(self, operation: str, kind: str) -> None:
        self.operation = operation
        self.kind = kind
        super().__init__(f"Suwappu {operation} failed: {kind}")


class SuwappuProtocolError(SuwappuRuntimeError):
    """A successful HTTP response violated the SDK/application contract."""

    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(f"Suwappu {operation} returned an invalid successful response")


def operation_timeout_seconds() -> float:
    """Return the host's bounded per-operation deadline.

    The SDK currently has a 30 second HTTP deadline, so accepting a larger
    adapter deadline would imply a guarantee this layer cannot provide.
    """

    raw = os.environ.get(
        "SUWAPPU_OPERATION_TIMEOUT_SECONDS",
        str(_DEFAULT_OPERATION_TIMEOUT_SECONDS),
    )
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError("SUWAPPU_OPERATION_TIMEOUT_SECONDS must be a number") from exc
    if not 0.01 <= value <= _MAX_OPERATION_TIMEOUT_SECONDS:
        raise ValueError(
            "SUWAPPU_OPERATION_TIMEOUT_SECONDS must be between 0.01 and 30 seconds"
        )
    return value


def _emit_event(
    *,
    operation: str,
    outcome: str,
    started_at: float,
    status: int | None = None,
) -> None:
    event: dict[str, Any] = {
        "operation": operation,
        "outcome": outcome,
        "duration_ms": round((time.monotonic() - started_at) * 1000, 1),
    }
    if status is not None:
        event["status"] = status
    logger.info("suwappu_api_event %s", json.dumps(event, sort_keys=True))


async def call_suwappu(
    operation: str,
    awaitable: Awaitable[_T],
    *,
    validator: Callable[[_T], None] | None = None,
) -> _T:
    """Run one SDK operation behind the adapter's observable deadline."""

    started_at = time.monotonic()
    try:
        result = await asyncio.wait_for(
            awaitable,
            timeout=operation_timeout_seconds(),
        )
        if validator is not None:
            validator(result)
    except asyncio.TimeoutError as exc:
        _emit_event(operation=operation, outcome="timeout", started_at=started_at)
        raise SuwappuTransportError(operation, "timeout") from exc
    except SuwappuProtocolError:
        _emit_event(
            operation=operation, outcome="protocol_error", started_at=started_at
        )
        raise
    except SuwappuError as exc:
        if exc.status == 200:
            _emit_event(
                operation=operation, outcome="protocol_error", started_at=started_at
            )
            raise SuwappuProtocolError(operation) from exc
        _emit_event(
            operation=operation,
            outcome="http_error",
            started_at=started_at,
            status=exc.status,
        )
        raise
    except ValidationError as exc:
        _emit_event(
            operation=operation, outcome="protocol_error", started_at=started_at
        )
        raise SuwappuProtocolError(operation) from exc
    except (httpx.TransportError, OSError) as exc:
        _emit_event(operation=operation, outcome="network_error", started_at=started_at)
        raise SuwappuTransportError(operation, "network_error") from exc
    else:
        _emit_event(operation=operation, outcome="success", started_at=started_at)
        return result
