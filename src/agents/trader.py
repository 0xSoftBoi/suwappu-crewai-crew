"""Trade planner — quote, simulate, prepare, and reconcile; never broadcast."""

from crewai import Agent

from src.tools.suwappu_tools import (
    get_quote,
    get_swap_history,
    list_managed_wallets,
    prepare_swap,
    simulate_swap,
)

SAFE_TRADE_TOOLS = [
    get_quote,
    simulate_swap,
    prepare_swap,
    list_managed_wallets,
    get_swap_history,
]


def create_trader_agent() -> Agent:
    return Agent(
        role="Trade Planner",
        goal="Build exact, risk-constrained plans from fresh quotes and simulations",
        backstory=(
            "You are a precise Suwappu trade planner. You can quote, dry-run, prepare "
            "unsigned self-custody transactions, and inspect managed swap history. "
            "Managed execution is intentionally outside your tool surface."
        ),
        tools=SAFE_TRADE_TOOLS,
        max_iter=6,
        allow_delegation=False,
        verbose=False,
    )

