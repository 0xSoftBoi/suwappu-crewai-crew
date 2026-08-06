"""Trader agent — quotes/simulates by default; managed execution is opt-in."""

from crewai import Agent

from src.tools.suwappu_tools import execute_swap, get_quote, simulate_swap


def create_trader_agent(*, enable_execution: bool = False) -> Agent:
    tools = [get_quote, simulate_swap]
    if enable_execution:
        tools.append(execute_swap)

    mode = "live managed execution is explicitly enabled" if enable_execution else "live execution is disabled"
    return Agent(
        role="Trade Planner" if not enable_execution else "Trade Executor",
        goal=(
            "Build precise, risk-constrained swap plans from fresh quotes. "
            + (
                "Submit only host-approved managed swaps."
                if enable_execution
                else "Simulate when possible and stop before broadcast."
            )
        ),
        backstory=(
            "You are a precise Suwappu trade operator. You distinguish quoting, "
            "simulation, and managed execution and never claim a transaction was "
            f"submitted unless the execution tool returns one. For this run, {mode}. "
            "Human approval is enforced by the host application, not by prompt text."
        ),
        tools=tools,
        verbose=True,
    )
