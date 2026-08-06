"""Market Analyst Agent — monitors prices and identifies opportunities."""

from crewai import Agent

from src.tools.suwappu_tools import get_prices, list_chains, list_tokens, get_portfolio


def create_analyst_agent() -> Agent:
    return Agent(
        role="Market Analyst",
        goal="Analyze token prices and identify trading opportunities across chains",
        backstory=(
            "You are an experienced DeFi market analyst who monitors cross-chain "
            "token prices. You identify arbitrage opportunities, price trends, and "
            "portfolio imbalances. You use the Suwappu API to fetch real-time data "
            "across 14 supported blockchain networks."
        ),
        tools=[get_prices, list_chains, list_tokens, get_portfolio],
        verbose=True,
    )
