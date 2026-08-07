import asyncio

import pytest

from src.tools import suwappu_tools


class FakeModel:
    def __init__(self, **values):
        self.__dict__.update(values)

    def model_dump(self):
        return dict(self.__dict__)


class FakeClient:
    def __init__(self, *, would_execute=True, execute_error=None):
        self.agent = self
        self.would_execute = would_execute
        self.execute_error = execute_error
        self.executions = []
        self.simulations = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def list_wallets(self):
        return [FakeModel(address="0xmanaged")]

    async def simulate_swap(self, *, quote_id, wallet_address):
        self.simulations.append((quote_id, wallet_address))
        return FakeModel(
            would_execute=self.would_execute,
            warnings=[] if self.would_execute else ["policy check failed"],
            quote_id=quote_id,
        )

    async def execute_managed_swap(self, quote_id, *, idempotency_key=None):
        self.executions.append((quote_id, idempotency_key))
        if self.execute_error:
            raise self.execute_error
        return FakeModel(swap_id=4812, status="pending", tx_hash=None)


@pytest.mark.parametrize(
    "value",
    ["rebalance-2026-08-06-001", "acct_1:trade.9"],
)
def test_idempotency_key_accepts_durable_safe_ids(value):
    assert suwappu_tools._validate_idempotency_key(value) == value


@pytest.mark.parametrize("value", ["", "bad key", "x" * 65, "slash/not-allowed"])
def test_idempotency_key_rejects_unsafe_ids(value):
    with pytest.raises(ValueError):
        suwappu_tools._validate_idempotency_key(value)


def test_managed_execution_requires_host_environment_gate(monkeypatch):
    monkeypatch.delenv("SUWAPPU_ALLOW_MANAGED_EXECUTION", raising=False)
    with pytest.raises(RuntimeError, match="disabled"):
        asyncio.run(
            suwappu_tools.execute_approved_managed_swap(
                quote_id="q_123", approved_intent_id="intent-123"
            )
        )


def test_managed_execution_resimulates_and_forwards_idempotency(monkeypatch):
    fake = FakeClient()
    monkeypatch.setenv("SUWAPPU_ALLOW_MANAGED_EXECUTION", "1")
    monkeypatch.setattr(suwappu_tools, "_get_client", lambda: fake)

    receipt = asyncio.run(
        suwappu_tools.execute_approved_managed_swap(
            quote_id="q_123", approved_intent_id="intent-123"
        )
    )

    assert fake.simulations == [("q_123", "0xmanaged")]
    assert fake.executions == [("q_123", "intent-123")]
    assert receipt["execution"]["swap_id"] == 4812


def test_failed_simulation_never_calls_execution(monkeypatch):
    fake = FakeClient(would_execute=False)
    monkeypatch.setenv("SUWAPPU_ALLOW_MANAGED_EXECUTION", "1")
    monkeypatch.setattr(suwappu_tools, "_get_client", lambda: fake)

    with pytest.raises(RuntimeError, match="policy check failed"):
        asyncio.run(
            suwappu_tools.execute_approved_managed_swap(
                quote_id="q_123", approved_intent_id="intent-123"
            )
        )
    assert fake.executions == []


def test_transport_failure_is_reported_as_unknown_outcome(monkeypatch):
    fake = FakeClient(execute_error=ConnectionError("socket closed"))
    monkeypatch.setenv("SUWAPPU_ALLOW_MANAGED_EXECUTION", "1")
    monkeypatch.setattr(suwappu_tools, "_get_client", lambda: fake)

    with pytest.raises(RuntimeError, match="outcome may be unknown") as exc_info:
        asyncio.run(
            suwappu_tools.execute_approved_managed_swap(
                quote_id="q_123", approved_intent_id="intent-123"
            )
        )
    assert "same approved_intent_id" in str(exc_info.value)
