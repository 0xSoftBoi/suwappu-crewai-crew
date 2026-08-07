"""Suwappu CrewAI reference: agents plan; the host owns live execution."""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Literal

from crewai import Crew, Process, Task
from pydantic import BaseModel, Field
from suwappu import SuwappuError

from src.agents.analyst import create_analyst_agent
from src.agents.risk import create_risk_agent
from src.agents.trader import create_trader_agent
from src.tools.suwappu_tools import execute_approved_managed_swap


class TradeCandidate(BaseModel):
    """One actionable candidate surfaced by the planning crew."""

    quote_id: str
    route: str = ""
    from_chain: str | None = None
    to_chain: str | None = None
    amount_in: str = ""
    expected_amount_out: str = ""
    wallet_address: str | None = None
    simulation_would_execute: bool | None = None
    expires_in_seconds: int | None = None


class TradePlan(BaseModel):
    """Stable application-facing output from the final CrewAI task."""

    summary: str
    risk_notes: list[str] = Field(default_factory=list)
    candidates: list[TradeCandidate] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    approval_required: Literal[True] = True
    executed: Literal[False] = False


def sanitize_query(query: str) -> str:
    """Normalize user text without pretending a keyword filter stops injection."""
    query = query.strip()
    if not query:
        raise ValueError("Query must not be empty")
    if len(query) > 2_000:
        raise ValueError("Query is too long (max 2000 characters)")
    return query


class TradingCrew:
    """Analyst + risk reviewer + trade planner with no broadcast-capable tool."""

    def __init__(self) -> None:
        self.analyst = create_analyst_agent()
        self.risk_reviewer = create_risk_agent()
        self.trade_planner = create_trader_agent()

    def run(self, query: str) -> TradePlan:
        safe_query = sanitize_query(query)

        analysis_task = Task(
            description=(
                "Analyze this user request using fresh Suwappu data where useful. "
                "Separate observed tool data from inference and never invent live "
                f"product capabilities: {safe_query}"
            ),
            expected_output="Evidence-grounded market and portfolio analysis",
            agent=self.analyst,
        )

        risk_task = Task(
            description=(
                "Review the analysis. Identify missing wallet/route evidence, exposure "
                "risks, simulation requirements, and explicit constraints. A quote or "
                "simulation is not evidence that a transaction executed."
            ),
            expected_output="Risk review with constraints and evidence gaps",
            agent=self.risk_reviewer,
            context=[analysis_task],
        )

        trade_task = Task(
            description=(
                "Build a non-broadcasting plan from fresh quotes. For a managed-wallet "
                "candidate, discover the managed wallet and bind the quote to it; "
                "simulate before recommending execution. For self-custody, you may "
                "prepare an unsigned transaction. Never claim funds moved. Return exact "
                "quote ids and expiry when available. Set approval_required=true and "
                "executed=false. Managed submission happens only in separate host code."
            ),
            expected_output=(
                "A structured TradePlan containing summary, risk_notes, candidates, "
                "next_steps, approval_required=true, and executed=false"
            ),
            agent=self.trade_planner,
            context=[analysis_task, risk_task],
            output_pydantic=TradePlan,
        )

        crew = Crew(
            agents=[self.analyst, self.risk_reviewer, self.trade_planner],
            tasks=[analysis_task, risk_task, trade_task],
            process=Process.sequential,
            cache=False,
            memory=False,
            share_crew=False,
            verbose=False,
        )
        result = crew.kickoff()
        if isinstance(result.pydantic, TradePlan):
            return result.pydantic
        return TradePlan.model_validate(result.to_dict())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Suwappu CrewAI: plan safely, or submit one pre-approved exact quote"
    )
    parser.add_argument(
        "query", nargs="?", help="Natural-language request for the planning crew"
    )
    parser.add_argument(
        "--execute-quote",
        metavar="QUOTE_ID",
        help="Bypass the crew and submit this exact pre-approved managed-wallet quote",
    )
    parser.add_argument(
        "--approved-intent-id",
        metavar="ID",
        help="Durable host-generated intent id forwarded as Suwappu's Idempotency-Key",
    )
    parser.add_argument("--execute", action="store_true", help=argparse.SUPPRESS)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.execute:
        parser.error(
            "--execute was removed: run the planning crew first, then use "
            "--execute-quote QUOTE_ID --approved-intent-id ID for the exact approved quote"
        )

    if args.execute_quote:
        if args.query:
            parser.error("do not send a model query when --execute-quote is used")
        if not args.approved_intent_id:
            parser.error("--execute-quote requires --approved-intent-id")
        try:
            receipt = asyncio.run(
                execute_approved_managed_swap(
                    quote_id=args.execute_quote,
                    approved_intent_id=args.approved_intent_id,
                )
            )
        except (SuwappuError, RuntimeError, ValueError) as exc:
            parser.exit(2, f"Managed execution stopped: {exc}\n")
        print(json.dumps(receipt, indent=2, sort_keys=True, default=str))
        return

    if args.approved_intent_id:
        parser.error("--approved-intent-id is only valid with --execute-quote")
    if not args.query:
        parser.error("a planning query is required")

    plan = TradingCrew().run(args.query)
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
