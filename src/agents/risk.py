"""Risk Manager Agent — validates trades and checks portfolio exposure."""

from crewai import Agent

from src.tools.suwappu_tools import get_portfolio, get_prices


def create_risk_agent() -> Agent:
    return Agent(
        role="Risk Manager",
        goal="Validate proposed trades and check portfolio exposure limits",
        backstory=(
            "You are a cautious risk manager. You review every trade proposal to ensure "
            "it doesn't exceed position limits, expose the portfolio to excessive "
            "concentration risk, or trade during high-volatility periods. You check "
            "current portfolio state and set guardrails for the trader."
        ),
        tools=[get_portfolio, get_prices],
        verbose=True,
    )
