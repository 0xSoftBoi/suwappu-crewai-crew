"""CrewAI tool wrappers for the current Suwappu Python SDK contract."""

from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from crewai.tools import tool
from suwappu import create_client


def _get_client():
    return create_client(api_key=os.environ.get("SUWAPPU_API_KEY", ""))


def _run_async(coro):
    """Run a coroutine from a synchronous CrewAI tool, even under an event loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    # asyncio.run() cannot nest inside an already-running loop. Run the
    # coroutine to completion on a dedicated thread instead of returning a
    # Future object to CrewAI.
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    return value


def _as_tool_output(value: Any) -> str:
    return json.dumps(_jsonable(value), default=str)


@tool("Get token prices")
def get_prices(symbols: str, chain: str = "") -> str:
    """Get current USD prices and 24h changes. symbols may be comma-separated."""
    async def _run():
        async with _get_client() as client:
            return await client.get_prices(symbols, chain or None)

    return _as_tool_output(_run_async(_run()))


@tool("Get swap quote")
def get_quote(from_token: str, to_token: str, amount: float, chain: str) -> str:
    """Get a swap quote. This is read-only and never moves funds."""
    if amount <= 0:
        raise ValueError("amount must be positive")

    async def _run():
        async with _get_client() as client:
            return await client.get_quote(from_token, to_token, amount, chain)

    return _as_tool_output(_run_async(_run()))


@tool("Simulate swap")
def simulate_swap(quote_id: str, wallet_address: str) -> str:
    """Dry-run a quote for a wallet. Never signs, broadcasts, or moves funds."""
    async def _run():
        async with _get_client() as client:
            return await client.simulate_swap(
                quote_id=quote_id,
                wallet_address=wallet_address,
            )

    return _as_tool_output(_run_async(_run()))


@tool("Execute managed swap")
def execute_swap(quote_id: str) -> str:
    """LIVE managed-wallet execution. Can broadcast a transaction and move funds."""
    if os.environ.get("SUWAPPU_ALLOW_MANAGED_EXECUTION") != "1":
        raise RuntimeError(
            "Managed execution is disabled. Set SUWAPPU_ALLOW_MANAGED_EXECUTION=1 "
            "and explicitly start the crew with --execute after host-level approval."
        )

    async def _run():
        async with _get_client() as client:
            return await client.execute_swap(quote_id)

    return _as_tool_output(_run_async(_run()))


@tool("Get portfolio")
def get_portfolio(wallet_address: str, chain: str = "") -> str:
    """Get balances for a wallet address, optionally filtered by chain."""
    if not wallet_address:
        raise ValueError("wallet_address is required")

    async def _run():
        async with _get_client() as client:
            return await client.get_portfolio(wallet_address, chain or None)

    return _as_tool_output(_run_async(_run()))


@tool("List chains")
def list_chains() -> str:
    """List all supported blockchain networks."""
    async def _run():
        async with _get_client() as client:
            return await client.list_chains()

    return _as_tool_output(_run_async(_run()))


@tool("List tokens")
def list_tokens(chain: str) -> str:
    """List available tokens on a specific chain."""
    if not chain:
        raise ValueError("chain is required")

    async def _run():
        async with _get_client() as client:
            return await client.list_tokens(chain)

    return _as_tool_output(_run_async(_run()))
