---
name: suwappu-crewai-crew
description: Safe-by-default CrewAI example — analyst, risk manager, and trader plan with Suwappu; managed execution is explicit opt-in
user-invocable: true
tools:
  - run_crew
metadata:
  openclaw.requires.env: ["SUWAPPU_API_KEY", "OPENAI_API_KEY"]
  openclaw.primaryEnv: SUWAPPU_API_KEY
  openclaw.emoji: "🤖"
  openclaw.category: defi
  openclaw.tags: ["crewai", "multi-agent", "trading", "defi", "analysis"]
---

# Suwappu CrewAI

Three agents collaborate on a request:

1. **Analyst** — fetches prices and discovery data across Suwappu's supported chains.
2. **Risk Manager** — reviews wallet exposure and proposed constraints.
3. **Trade Planner** — gets quotes and simulations; managed execution is absent by default.

## Setup

The CrewAI package and the Suwappu Python SDK are not currently published together on PyPI. Install this repository so its pinned SDK source dependency is used:

```bash
git clone https://github.com/0xSoftBoi/suwappu-crewai-crew.git
cd suwappu-crewai-crew
python -m pip install -e .
export SUWAPPU_API_KEY=suwappu_sk_...
export OPENAI_API_KEY=sk-...
```

## Usage

Safe default:

```bash
suwappu-crew "Analyze ETH across chains and propose a rebalancing plan"
```

Live managed execution is a separate host-approved mode and requires both:

```bash
export SUWAPPU_ALLOW_MANAGED_EXECUTION=1
suwappu-crew --execute "Execute the approved plan"
```

Do not treat prompt text as approval. Configure Suwappu wallet policies and an application-level approval boundary before enabling managed execution.
