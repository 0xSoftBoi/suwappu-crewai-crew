import asyncio
import logging

import pytest
from suwappu import SuwappuError

from src.runtime import (
    SuwappuProtocolError,
    SuwappuTransportError,
    call_suwappu,
    operation_timeout_seconds,
)


async def _return(value):
    return value


async def _raise(error):
    raise error


def test_success_event_contains_metadata_not_response(caplog):
    caplog.set_level(logging.INFO, logger="suwappu_crewai.api")
    secret_response = {"wallet": "0xprivate", "api_key": "suwappu_sk_secret"}

    result = asyncio.run(call_suwappu("get_portfolio", _return(secret_response)))

    assert result == secret_response
    assert "get_portfolio" in caplog.text
    assert '"outcome": "success"' in caplog.text
    assert "0xprivate" not in caplog.text
    assert "suwappu_sk_secret" not in caplog.text


def test_http_error_preserves_sdk_error_and_status_metadata(caplog):
    caplog.set_level(logging.INFO, logger="suwappu_crewai.api")
    error = SuwappuError(429, "private upstream body")

    with pytest.raises(SuwappuError) as exc_info:
        asyncio.run(call_suwappu("get_quote", _raise(error)))

    assert exc_info.value is error
    assert '"status": 429' in caplog.text
    assert "private upstream body" not in caplog.text


def test_sdk_malformed_200_becomes_protocol_error(caplog):
    caplog.set_level(logging.INFO, logger="suwappu_crewai.api")

    with pytest.raises(SuwappuProtocolError):
        asyncio.run(
            call_suwappu(
                "execute_managed_swap",
                _raise(SuwappuError(200, "malformed secret response")),
            )
        )

    assert '"outcome": "protocol_error"' in caplog.text
    assert "malformed secret response" not in caplog.text


def test_operation_timeout_is_typed(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="suwappu_crewai.api")
    monkeypatch.setenv("SUWAPPU_OPERATION_TIMEOUT_SECONDS", "0.01")

    async def slow():
        await asyncio.sleep(0.1)

    with pytest.raises(SuwappuTransportError) as exc_info:
        asyncio.run(call_suwappu("list_chains", slow()))

    assert exc_info.value.kind == "timeout"
    assert '"outcome": "timeout"' in caplog.text


@pytest.mark.parametrize("value", ["0", "31", "not-a-number"])
def test_operation_timeout_rejects_invalid_configuration(monkeypatch, value):
    monkeypatch.setenv("SUWAPPU_OPERATION_TIMEOUT_SECONDS", value)
    with pytest.raises(ValueError):
        operation_timeout_seconds()
