"""Trade Executor Agent — executes optimal swaps via Suwappu."""

from crewai import Agent

from src.tools.suwappu_tools import get_quote, execute_swap


def create_trader_agent() -> Agent:
    return Agent(
        role="Trade Executor",
        goal="Execute optimal token swaps based on analysis and risk parameters",
        backstory=(
            "You are a precise trade executor. You take the analyst's recommendations "
            "and the risk manager's constraints, then execute swaps via the Suwappu DEX. "
            "You always get a quote first, present the details, and only execute if the "
            "trade meets the risk parameters."
        ),
        tools=[get_quote, execute_swap],
        verbose=True,
    )
