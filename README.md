# suwappu-crewai-crew

**Multi-agent trading crew powered by [CrewAI](https://crewai.com) and the [Suwappu](https://suwappu.bot) cross-chain DEX.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.80+-green.svg)](https://crewai.com)

Three specialized AI agents collaborate to analyze markets, assess risk, and execute trades across 15 blockchain networks.

---

## Architecture

```
          ┌─────────────────┐
          │   User Query     │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  Market Analyst  │ ── get_prices, list_chains, get_portfolio
          │  Fetches data,   │
          │  spots trends    │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  Risk Manager    │ ── get_portfolio, get_prices
          │  Checks exposure,│
          │  sets guardrails │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │ Trade Executor   │ ── get_quote, execute_swap
          │  Gets quotes,    │
          │  executes swaps  │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  Execution Report │
          └─────────────────┘
```

---

## Features

- **3 specialized agents** — Analyst, Risk Manager, Trader
- **Configurable via YAML** — Agent roles and task definitions in config files
- **5 Suwappu tools** — Prices, quotes, swaps, portfolio, chains
- **15 chains** — Ethereum, Arbitrum, Base, Solana, and more
- **Natural language** — Just describe what you want: "Rebalance my portfolio to 50/30/20"
- **OpenClaw compatible** — Includes SKILL.md for AI agent discovery

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/0xSoftBoi/suwappu-crewai-crew.git
cd suwappu-crewai-crew

# 2. Install
pip install -e .
# or
uv pip install -e .

# 3. Set API keys
export SUWAPPU_API_KEY=suwappu_sk_...   # Get free at POST https://api.suwappu.bot/v1/agent/register
export OPENAI_API_KEY=sk-...             # CrewAI uses an LLM backend

# 4. Run
suwappu-crew "Analyze ETH prices across Arbitrum, Base, and Optimism"
```

---

## Example Queries

```bash
# Market analysis
suwappu-crew "What are the best prices for ETH across all chains?"

# Portfolio rebalancing
suwappu-crew "Check my portfolio and suggest trades to reach 50% ETH, 30% SOL, 20% USDC"

# Opportunity finding
suwappu-crew "Find the cheapest chain to buy WBTC right now"

# Risk assessment
suwappu-crew "Is my portfolio too concentrated? Suggest diversification trades."
```

---

## Agents

### Market Analyst
- **Role**: Monitors prices, identifies trends and opportunities
- **Tools**: `get_prices`, `list_chains`, `get_portfolio`
- **Output**: Market analysis with data-backed recommendations

### Risk Manager
- **Role**: Validates trade proposals against portfolio exposure
- **Tools**: `get_portfolio`, `get_prices`
- **Output**: Risk assessment with max position sizes and warnings

### Trade Executor
- **Role**: Gets quotes and executes approved swaps
- **Tools**: `get_quote`, `execute_swap`
- **Output**: Execution report with transaction hashes

---

## Configuration

Agent and task definitions live in `src/config/`:

**`agents.yaml`** — Agent roles, goals, and backstories
**`tasks.yaml`** — Task descriptions and expected outputs

Modify these to customize agent behavior without changing code.

---

## Project Structure

```
suwappu-crewai-crew/
├── pyproject.toml             # Package config
├── SKILL.md                   # OpenClaw skill definition
├── src/
│   ├── crew.py                # Crew orchestration + CLI
│   ├── agents/
│   │   ├── analyst.py         # Market analysis agent
│   │   ├── trader.py          # Trade execution agent
│   │   └── risk.py            # Risk management agent
│   ├── tools/
│   │   └── suwappu_tools.py   # CrewAI @tool wrappers for Suwappu
│   └── config/
│       ├── agents.yaml        # Agent definitions
│       └── tasks.yaml         # Task definitions
└── examples/
    └── run_crew.py            # Example script
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUWAPPU_API_KEY` | Yes | Suwappu API key ([get one free](https://api.suwappu.bot/v1/agent/register)) |
| `OPENAI_API_KEY` | Yes | LLM backend for CrewAI agents |

---

## License

[MIT](LICENSE)
