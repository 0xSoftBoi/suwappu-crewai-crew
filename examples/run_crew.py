"""Minimal example: produce a structured Suwappu TradePlan with CrewAI."""

from src.crew import TradingCrew


def main() -> None:
    crew = TradingCrew()
    plan = crew.run(
        "Compare ETH routes for 100 USDC on Base. If a wallet is needed, "
        "say so explicitly. Quote and simulate if possible; do not execute."
    )
    print(plan.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

