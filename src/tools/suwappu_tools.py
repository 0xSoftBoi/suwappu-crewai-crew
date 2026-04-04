"""CrewAI tool wrappers for the Suwappu DEX API."""

from __future__ import annotations

import asyncio
import os

from crewai.tools import tool

from suwappu import create_client

MAX_TRADE_USD = float(os.environ.get("SUWAPPU_MAX_TRADE_USD", "100"))


def _get_client():
    api_key = os.environ.get("SUWAPPU_API_KEY", "")
    return create_client(api_key=api_key)


def _run_async(coro):
    """Run async code in sync context."""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return loop.run_in_executor(pool, lambda: asyncio.run(coro))
    except RuntimeError:
        return asyncio.run(coro)


@tool("Get token prices")
def get_prices(token: str, chain: str = "") -> str:
    """Get current USD price and 24h change for a token. Optionally specify a chain."""
    async def _run():
        client = _get_client()
        result = await client.get_prices(token, chain or None)
        await client.close()
        return result.model_dump() if hasattr(result, "model_dump") else str(result)
    return str(_run_async(_run()))


@tool("Get swap quote")
def get_quote(from_token: str, to_token: str, amount: float, chain: str) -> str:
    """Get a swap quote for trading tokens. Returns price, route, gas, and fees."""
    async def _run():
        client = _get_client()
        result = await client.get_quote(from_token, to_token, amount, chain)
        await client.close()
        return result.model_dump() if hasattr(result, "model_dump") else str(result)
    return str(_run_async(_run()))


@tool("Execute swap")
def execute_swap(quote_id: str) -> str:
    """Execute a previously quoted swap. Returns transaction hash and status."""
    if not os.environ.get("SUWAPPU_MAX_TRADE_USD"):
        raise ValueError(
            "SUWAPPU_MAX_TRADE_USD must be set before executing trades. "
            "Set to your max allowed trade in USD."
        )

    async def _run():
        client = _get_client()
        result = await client.execute_swap(quote_id)
        await client.close()
        return result.model_dump() if hasattr(result, "model_dump") else str(result)
    return str(_run_async(_run()))


@tool("Get portfolio")
def get_portfolio(chain: str = "") -> str:
    """Check wallet token balances across all chains or a specific chain."""
    async def _run():
        client = _get_client()
        result = await client.get_portfolio(chain or None)
        await client.close()
        return [r.model_dump() if hasattr(r, "model_dump") else str(r) for r in result]
    return str(_run_async(_run()))


@tool("List chains")
def list_chains() -> str:
    """List all supported blockchain networks."""
    async def _run():
        client = _get_client()
        result = await client.list_chains()
        await client.close()
        return [r.model_dump() if hasattr(r, "model_dump") else str(r) for r in result]
    return str(_run_async(_run()))


@tool("List tokens")
def list_tokens(chain: str) -> str:
    """List all available tokens on a specific chain."""
    async def _run():
        client = _get_client()
        result = await client.list_tokens(chain)
        await client.close()
        return [r.model_dump() if hasattr(r, "model_dump") else str(r) for r in result]
    return str(_run_async(_run()))
