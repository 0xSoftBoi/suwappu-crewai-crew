---
name: suwappu-crewai-crew
description: Multi-agent trading crew — 3 AI agents (analyst, trader, risk manager) collaborate to analyze markets and execute trades
user-invocable: true
tools:
  - run_crew
metadata:
  openclaw.requires.env: ["SUWAPPU_API_KEY", "OPENAI_API_KEY"]
  openclaw.primaryEnv: SUWAPPU_API_KEY
  openclaw.emoji: "🤖"
  openclaw.category: defi
  openclaw.tags: ["crewai", "multi-agent", "trading", "defi", "analysis"]
  openclaw.install:
    - type: pip
      package: "suwappu-crewai-crew"
---

# Suwappu CrewAI Trading Crew

Three specialized AI agents collaborate on a single trading query:

1. **Analyst** — Fetches prices, identifies opportunities across 15 chains
2. **Risk Manager** — Checks portfolio exposure, sets guardrails
3. **Trader** — Gets quotes, executes swaps within risk parameters

## Setup

```bash
pip install suwappu-crewai-crew
export SUWAPPU_API_KEY=suwappu_sk_...
export OPENAI_API_KEY=sk-...
```

## Usage

```bash
suwappu-crew "Analyze ETH across chains and suggest rebalancing trades"
```
