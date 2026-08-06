"""Suwappu CrewAI example — analysis by default, managed execution by opt-in."""

from __future__ import annotations

import argparse
import os

from crewai import Crew, Task

from src.agents.analyst import create_analyst_agent
from src.agents.risk import create_risk_agent
from src.agents.trader import create_trader_agent


def sanitize_query(query: str) -> str:
    """Normalize user text without pretending keyword filters stop prompt injection."""
    query = query.strip()
    if not query:
        raise ValueError("Query must not be empty")
    if len(query) > 2_000:
        raise ValueError("Query is too long (max 2000 characters)")
    return query


class TradingCrew:
    """Analyst + risk manager + trader, with live execution disabled by default."""

    def __init__(self, *, enable_execution: bool = False) -> None:
        self.enable_execution = enable_execution
        self.analyst = create_analyst_agent()
        self.risk_manager = create_risk_agent()
        self.trader = create_trader_agent(enable_execution=enable_execution)

    def run(self, query: str) -> str:
        """Run the crew with a user query."""
        safe_query = sanitize_query(query)

        analysis_task = Task(
            description=f"Analyze the following request and provide market insights: {safe_query}",
            expected_output="Market analysis grounded in Suwappu tool results",
            agent=self.analyst,
        )

        risk_task = Task(
            description=(
                "Review the analysis and assess portfolio risk. If portfolio data is "
                "needed, require a wallet address. Recommend constraints and identify "
                "what should be simulated before any live action."
            ),
            expected_output="Risk assessment, constraints, and simulation recommendations",
            agent=self.risk_manager,
        )

        if self.enable_execution:
            trade_description = (
                "Use fresh Suwappu quotes and the risk assessment. Managed execution is "
                "enabled by the host for this run; execute only actions that satisfy the "
                "host-approved scope, and report the returned swap id/status exactly."
            )
            trade_output = "Execution report with quote ids, swap ids/status, and any transaction hashes"
        else:
            trade_description = (
                "Plan the trade using fresh quotes. Simulate when a wallet address is "
                "available. Do not execute, broadcast, or claim that funds moved; return "
                "an execution plan for human review."
            )
            trade_output = "Non-executing trade plan with quotes, simulations, and approval requirements"

        trade_task = Task(
            description=trade_description,
            expected_output=trade_output,
            agent=self.trader,
        )

        crew = Crew(
            agents=[self.analyst, self.risk_manager, self.trader],
            tasks=[analysis_task, risk_task, trade_task],
            verbose=False,
        )

        return str(crew.kickoff())


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Suwappu CrewAI example (analysis-only unless --execute is set)"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="Analyze ETH prices across chains and suggest rebalancing trades",
        help="Query for the crew",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Expose live Suwappu managed-wallet execution. Also requires "
            "SUWAPPU_ALLOW_MANAGED_EXECUTION=1."
        ),
    )
    args = parser.parse_args()

    if args.execute and os.environ.get("SUWAPPU_ALLOW_MANAGED_EXECUTION") != "1":
        parser.error(
            "--execute also requires SUWAPPU_ALLOW_MANAGED_EXECUTION=1 "
            "after host-level approval"
        )

    result = TradingCrew(enable_execution=args.execute).run(args.query)
    print("\n" + "=" * 60)
    print("CREW RESULT:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()
