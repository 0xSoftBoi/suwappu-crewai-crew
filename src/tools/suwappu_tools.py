"""CrewAI tools plus a deliberately non-agent managed-execution boundary."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from crewai.tools import tool
from suwappu import SuwappuError, create_client

_IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")


def _get_client():
    return create_client(api_key=os.environ.get("SUWAPPU_API_KEY", ""))


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _as_tool_output(value: Any) -> str:
    return json.dumps(_jsonable(value), default=str, sort_keys=True)


def _validate_idempotency_key(value: str) -> str:
    key = value.strip()
    if not _IDEMPOTENCY_KEY.fullmatch(key):
        raise ValueError(
            "approved_intent_id must be 1-64 characters using only "
            "letters, numbers, _, ., :, or -"
        )
    return key


@tool("Get token prices")
async def get_prices(symbols: str, chain: str = "") -> str:
    """Get current USD prices and 24h changes. symbols may be comma-separated."""
    async with _get_client() as client:
        return _as_tool_output(await client.get_prices(symbols, chain or None))


@tool("Get swap quote")
async def get_quote(
    from_token: str,
    to_token: str,
    amount: float,
    chain: str = "",
    from_chain: str = "",
    to_chain: str = "",
    wallet_address: str = "",
    slippage: float | None = None,
) -> str:
    """Get a same-chain or cross-chain quote. This never moves funds."""
    if amount <= 0:
        raise ValueError("amount must be positive")
    if chain and (from_chain or to_chain):
        raise ValueError("use chain for same-chain quotes or from_chain/to_chain for cross-chain quotes")
    if bool(from_chain) != bool(to_chain):
        raise ValueError("cross-chain quotes require both from_chain and to_chain")
    if not chain and not (from_chain and to_chain):
        raise ValueError("provide chain or both from_chain and to_chain")

    async with _get_client() as client:
        value = await client.get_quote(
            from_token,
            to_token,
            amount,
            chain or None,
            wallet_address=wallet_address or None,
            from_chain=from_chain or None,
            to_chain=to_chain or None,
            slippage=slippage,
        )
        return _as_tool_output(value)


@tool("Simulate swap")
async def simulate_swap(quote_id: str, wallet_address: str) -> str:
    """Dry-run a quote for a wallet. Never signs, broadcasts, or moves funds."""
    if not quote_id.strip() or not wallet_address.strip():
        raise ValueError("quote_id and wallet_address are required")
    async with _get_client() as client:
        value = await client.simulate_swap(
            quote_id=quote_id.strip(),
            wallet_address=wallet_address.strip(),
        )
        return _as_tool_output(value)


@tool("Prepare unsigned swap")
async def prepare_swap(quote_id: str, wallet_address: str) -> str:
    """Build an unsigned self-custody transaction. Never signs or broadcasts."""
    if not quote_id.strip() or not wallet_address.strip():
        raise ValueError("quote_id and wallet_address are required")
    async with _get_client() as client:
        value = await client.prepare_swap(
            quote_id=quote_id.strip(),
            wallet_address=wallet_address.strip(),
        )
        return _as_tool_output(value)


@tool("Get portfolio")
async def get_portfolio(wallet_address: str, chain: str = "") -> str:
    """Get balances for a wallet address, optionally filtered by chain."""
    if not wallet_address.strip():
        raise ValueError("wallet_address is required")
    async with _get_client() as client:
        value = await client.get_portfolio(wallet_address.strip(), chain or None)
        return _as_tool_output(value)


@tool("List chains")
async def list_chains() -> str:
    """List chains currently exposed by the Suwappu API."""
    async with _get_client() as client:
        return _as_tool_output(await client.list_chains())


@tool("List tokens")
async def list_tokens(chain: str) -> str:
    """List available tokens on a specific chain."""
    if not chain.strip():
        raise ValueError("chain is required")
    async with _get_client() as client:
        return _as_tool_output(await client.list_tokens(chain.strip()))


@tool("List managed wallets")
async def list_managed_wallets() -> str:
    """List this agent's managed wallet addresses. This is read-only."""
    async with _get_client() as client:
        return _as_tool_output(await client.agent.list_wallets())


@tool("Get managed swap history")
async def get_swap_history(status: str = "", limit: int = 20, offset: int = 0) -> str:
    """Read managed swap history for reconciliation. Never submits a transaction."""
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    async with _get_client() as client:
        value = await client.list_swaps(
            status=status.strip() or None,
            limit=limit,
            offset=offset,
        )
        return _as_tool_output(value)


async def execute_approved_managed_swap(
    *, quote_id: str, approved_intent_id: str
) -> dict[str, Any]:
    """Execute one exact quote outside the CrewAI tool surface.

    The host supplies a durable intent id. The function re-simulates the quote
    against the agent's managed wallet before submission and forwards the same
    intent id as Suwappu's Idempotency-Key.
    """
    if os.environ.get("SUWAPPU_ALLOW_MANAGED_EXECUTION") != "1":
        raise RuntimeError(
            "Managed execution is disabled; set SUWAPPU_ALLOW_MANAGED_EXECUTION=1 "
            "only after the host has approved the exact quote"
        )

    clean_quote_id = quote_id.strip()
    if not clean_quote_id or len(clean_quote_id) > 256:
        raise ValueError("quote_id must be between 1 and 256 characters")
    intent_id = _validate_idempotency_key(approved_intent_id)

    async with _get_client() as client:
        wallets = await client.agent.list_wallets()
        if len(wallets) != 1:
            raise RuntimeError(
                "Managed execution requires exactly one managed wallet for this agent; "
                f"found {len(wallets)}"
            )
        wallet = wallets[0]
        simulation = await client.simulate_swap(
            quote_id=clean_quote_id,
            wallet_address=wallet.address,
        )
        if not simulation.would_execute:
            warnings = "; ".join(simulation.warnings) or "simulation rejected the quote"
            raise RuntimeError(f"Refusing managed execution: {warnings}")

        try:
            result = await client.execute_managed_swap(
                clean_quote_id,
                idempotency_key=intent_id,
            )
        except SuwappuError as exc:
            if exc.status >= 500:
                raise RuntimeError(
                    "Managed execution returned a server error; outcome may be unknown. "
                    "Reconcile swap status/history before retrying the same quote with "
                    "the same approved_intent_id."
                ) from exc
            raise
        except Exception as exc:
            raise RuntimeError(
                "Managed execution transport failed; outcome may be unknown. Reconcile "
                "swap status/history before retrying the same quote with the same "
                "approved_intent_id."
            ) from exc

    return {
        "approved_intent_id": intent_id,
        "wallet_address": wallet.address,
        "simulation": _jsonable(simulation),
        "execution": _jsonable(result),
    }

