"""Market analyst agent — discovery and evidence, never execution."""

from crewai import Agent

from src.tools.suwappu_tools import get_portfolio, get_prices, list_chains, list_tokens

ANALYST_TOOLS = [get_prices, list_chains, list_tokens, get_portfolio]


def create_analyst_agent() -> Agent:
    return Agent(
        role="Market Analyst",
        goal="Ground market and portfolio observations in fresh Suwappu data",
        backstory=(
            "You are a DeFi market analyst. You distinguish observed API data from "
            "inference, never invent route quality or supported-network counts, and "
            "never claim that analysis moved funds."
        ),
        tools=ANALYST_TOOLS,
        max_iter=6,
        allow_delegation=False,
        verbose=False,
    )

