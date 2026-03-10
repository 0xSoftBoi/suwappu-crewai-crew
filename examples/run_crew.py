"""Example: Run the Suwappu Trading Crew."""

from src.crew import TradingCrew


def main():
    crew = TradingCrew()

    # Example queries
    queries = [
        "Analyze ETH prices across Arbitrum, Base, and Optimism. Suggest rebalancing trades.",
        "Check my portfolio and recommend swaps to reach 50% ETH, 30% SOL, 20% USDC.",
        "Find the best chain to buy ETH right now based on prices.",
    ]

    result = crew.run(queries[0])
    print(result)


if __name__ == "__main__":
    main()
