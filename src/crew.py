"""Suwappu Trading Crew — Multi-agent trading with CrewAI + Suwappu DEX."""

from __future__ import annotations

import argparse
import sys

from crewai import Crew, Task

from src.agents.analyst import create_analyst_agent
from src.agents.risk import create_risk_agent
from src.agents.trader import create_trader_agent


class TradingCrew:
    """Three-agent trading crew: analyst, trader, risk manager."""

    def __init__(self) -> None:
        self.analyst = create_analyst_agent()
        self.trader = create_trader_agent()
        self.risk_manager = create_risk_agent()

    def run(self, query: str) -> str:
        """Run the crew with a user query."""
        analysis_task = Task(
            description=f"Analyze the following request and provide market insights: {query}",
            expected_output="Market analysis with price data, trends, and opportunities",
            agent=self.analyst,
        )

        risk_task = Task(
            description="Review the analysis and assess portfolio risk. Check current portfolio exposure and recommend safe trade parameters.",
            expected_output="Risk assessment with max position sizes and warnings",
            agent=self.risk_manager,
        )

        trade_task = Task(
            description="Based on the analysis and risk assessment, plan and execute the optimal trades.",
            expected_output="Trade execution report with transaction hashes and final portfolio state",
            agent=self.trader,
        )

        crew = Crew(
            agents=[self.analyst, self.risk_manager, self.trader],
            tasks=[analysis_task, risk_task, trade_task],
            verbose=True,
        )

        result = crew.kickoff()
        return str(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Suwappu Trading Crew")
    parser.add_argument(
        "query",
        nargs="?",
        default="Analyze ETH prices across chains and suggest rebalancing trades",
        help="Trading query for the crew",
    )
    args = parser.parse_args()

    crew = TradingCrew()
    result = crew.run(args.query)
    print("\n" + "=" * 60)
    print("CREW RESULT:")
    print("=" * 60)
    print(result)


if __name__ == "__main__":
    main()
