"""Risk reviewer agent — challenges proposals without a live action tool."""

from crewai import Agent

from src.tools.suwappu_tools import get_portfolio, get_prices, get_swap_history

RISK_TOOLS = [get_portfolio, get_prices, get_swap_history]


def create_risk_agent() -> Agent:
    return Agent(
        role="Risk Reviewer",
        goal="Challenge trade proposals and make constraints explicit before approval",
        backstory=(
            "You are a cautious risk reviewer. You verify wallet exposure when an "
            "address is available, surface missing evidence, and separate simulation "
            "results from guarantees. You cannot submit transactions."
        ),
        tools=RISK_TOOLS,
        max_iter=6,
        allow_delegation=False,
        verbose=False,
    )
