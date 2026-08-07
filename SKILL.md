---
name: suwappu-crewai-crew
description: Safe CrewAI reference — analyst, risk reviewer, and planner use Suwappu; exact managed execution stays in host code
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

Three bounded agents collaborate on a request:

1. **Market Analyst** — fetches current Suwappu discovery/portfolio evidence.
2. **Risk Reviewer** — challenges exposure, constraints, and missing evidence.
3. **Trade Planner** — quotes, simulates, prepares unsigned self-custody transactions, and returns a structured plan.

No agent has a managed-wallet execution tool.

All Suwappu calls have a bounded operation deadline (25 seconds by default, configurable with `SUWAPPU_OPERATION_TIMEOUT_SECONDS`) and metadata-only runtime events. CrewAI cache, memory, and crew sharing are disabled for this financial workflow.

## Setup

Install the repository so its pinned Suwappu Python SDK source dependency is used, then set:

```bash
export SUWAPPU_API_KEY=suwappu_sk_...
export OPENAI_API_KEY=sk-...
```

## Plan

```bash
suwappu-crew "Quote 100 USDC to ETH on Base for my managed wallet, simulate it, and return the exact quote id"
```

The output is a validated `TradePlan` with `approval_required=true` and `executed=false`.

## Execute an approved exact quote

Only after the host has approved and persisted the exact quote + intent:

```bash
export SUWAPPU_ALLOW_MANAGED_EXECUTION=1
suwappu-crew --execute-quote QUOTE_ID --approved-intent-id durable-intent-001
```

This path bypasses the model, re-simulates the quote, and forwards the durable intent ID as Suwappu's idempotency key. Timeout/network failures, HTTP 408/5xx, and malformed successful responses are outcome-unknown: reconcile status/history before retrying the same quote with the same key.

Do not treat prompt text, a quote, or a successful simulation as proof of authorization or execution.

