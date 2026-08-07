# Suwappu CrewAI

A standalone, production-oriented [CrewAI](https://crewai.com) decision workflow for building agent products on [Suwappu](https://suwappu.bot). Three agents analyze, challenge risk, and produce a structured trade plan behind a bounded/observable API runtime. The agents can quote, simulate, prepare unsigned transactions, and reconcile managed-swap history. **No CrewAI agent has a live managed-execution tool.**

The core pattern is intentionally two-phase:

1. let the model produce an evidence-backed plan;
2. let deterministic host code approve and submit one exact quote.

That boundary matters more than another prompt saying “ask before trading.”

> **Repository visibility:** this repository is currently private. Clone commands require collaborator access until the owner makes it public. The canonical developer documentation lives at [suwappu.bot/docs](https://suwappu.bot/docs).

## Why this product is useful

CrewAI is strongest when separate roles add real value. This example gives each model a narrow job and keeps irreversible action outside the model loop:

| Role | Job | Suwappu access | Moves funds? |
|---|---|---|---:|
| Market Analyst | Ground the request in current price, chain, token, and portfolio data | Read-only | No |
| Risk Reviewer | Challenge exposure, evidence gaps, and proposed constraints | Read-only + history | No |
| Trade Planner | Quote, simulate, prepare unsigned self-custody transactions, return exact quote IDs | Non-broadcasting | No |
| Host approval boundary | Re-simulate one approved quote and submit with a durable idempotency key | Managed execution | **Yes** |

If one agent can do your job reliably, use one agent. A three-agent crew costs more model tokens and adds latency. Split roles only when the extra review or specialization measurably improves the product.

## Current compatibility

This repository targets CrewAI `1.15.x` (`>=1.15,<2`) and Python `>=3.10,<3.14`, matching CrewAI's current documented Python range. It uses CrewAI's native async custom tools and Pydantic task output instead of the old thread-wrapped synchronous tool pattern.

The Suwappu Python SDK dependency is pinned to the merged core commit `09da700efa2cdaf4a3074e2ab8e2c61cbb22fdb7` for a reproducible source install while the SDK release channel is still being normalized.

The financial crew explicitly uses `cache=False`, `memory=False`, and `share_crew=False`. Turning any of those on is a new data-freshness/tenant-isolation decision, not a harmless optimization.

## Quick start

```bash
git clone https://github.com/0xSoftBoi/suwappu-crewai-crew.git
cd suwappu-crewai-crew

python -m venv .venv
source .venv/bin/activate
python -m pip install -e .

export SUWAPPU_API_KEY=suwappu_sk_...
export OPENAI_API_KEY=sk-...

suwappu-crew "Quote 100 USDC to ETH on Base for my managed wallet, simulate it, and return the exact quote id for review"
```

Register a Suwappu agent if you do not already have an API key:

```bash
curl -X POST https://api.suwappu.bot/v1/agent/register \
  -H "Content-Type: application/json" \
  -d '{"name":"my-crewai-product"}'
```

The final CrewAI task is validated into a `TradePlan` instead of returning free-form text:

```json
{
  "summary": "...",
  "risk_notes": ["..."],
  "candidates": [
    {
      "quote_id": "...",
      "simulation_would_execute": true
    }
  ],
  "next_steps": ["Review the exact quote before managed submission"],
  "approval_required": true,
  "executed": false
}
```

## Managed execution: separate host action

After a human or application policy approves the exact `quote_id`, persist a durable intent ID in your application. Then call the host execution path:

```bash
export SUWAPPU_ALLOW_MANAGED_EXECUTION=1

suwappu-crew \
  --execute-quote YOUR_EXACT_QUOTE_ID \
  --approved-intent-id rebalance-2026-08-06-001
```

This command does **not** ask CrewAI what to execute. It:

1. validates the host-generated intent ID;
2. loads the Suwappu agent's managed wallet;
3. re-simulates the exact approved quote against that wallet;
4. refuses submission if the simulation says it would not execute; and
5. calls `execute_managed_swap()` with the intent ID as `Idempotency-Key`.

Do not generate idempotency keys from the current time at retry time. Persist one key per intended economic action. If submission hits a timeout/network failure, HTTP 408/5xx, or a malformed successful response, the outcome is unknown: reconcile the managed swap before retrying the **same quote with the same key**.

Given the returned `swap_id`, reconcile the specific managed swap with the REST status endpoint:

```bash
curl https://api.suwappu.bot/v1/agent/swap/status/4812 \
  -H "Authorization: Bearer $SUWAPPU_API_KEY"
```

The crew also has a read-only managed-swap-history tool for follow-up analysis.

## Enterprise runtime boundary

Every Suwappu SDK operation is wrapped by a product-controlled deadline and a metadata-only event:

~~~bash
export SUWAPPU_OPERATION_TIMEOUT_SECONDS=15
~~~

The default is 25 seconds; the accepted range is 0.01-30 seconds because the pinned SDK itself currently has a 30-second HTTP deadline. The `suwappu_crewai.api` logger emits operation, outcome, duration, and HTTP status when present. It does not emit prompts, tool arguments, credentials, wallets, quote/swap IDs, bodies, or exception messages.

Transport timeouts/network failures raise `SuwappuTransportError`. Malformed successful responses raise `SuwappuProtocolError`. A failure in the live submission window becomes `ManagedExecutionOutcomeUnknown`, which carries the durable intent ID for host reconciliation.

There is deliberately no generic retry wrapper. Reads, quotes, simulation, unsigned preparation, and managed execution have different retry semantics.

For tenant isolation, retry rules, persistent intent state, SLO/alert guidance, CrewAI tracing controls, dependency risk, deployment/rollback, and the live-money incident runbook, read [Operations](docs/OPERATIONS.md).

## Same-chain and cross-chain quotes

The quote tool exposes the current SDK contract:

- same-chain: `chain="base"`;
- cross-chain: `from_chain="base", to_chain="arbitrum"`;
- wallet-bound: include `wallet_address` before simulation or transaction preparation;
- optional: set `slippage` explicitly instead of hiding it in a prompt.

Ask for the parameters you actually need:

```bash
suwappu-crew "Quote 100 USDC on Base to ETH on Arbitrum for wallet 0x..., simulate it, and explain fees, route, expiry, and risks. Do not execute."
```

## Tool surface

| CrewAI tool | SDK call | Authority |
|---|---|---|
| Get token prices | `get_prices` | Read-only |
| Get swap quote | `get_quote` | Read-only |
| Simulate swap | `simulate_swap` | Dry-run |
| Prepare unsigned swap | `prepare_swap` | Builds only; no signing/broadcast |
| Get portfolio | `get_portfolio` | Read-only |
| List chains | `list_chains` | Read-only |
| List tokens | `list_tokens` | Read-only |
| List managed wallets | `client.agent.list_wallets` | Read-only |
| Get managed swap history | `list_swaps` | Read-only reconciliation |

`execute_approved_managed_swap()` is plain Python, not a CrewAI tool. Keeping that distinction visible is the point of this reference implementation.

## Build a product, not just a demo

A useful commercial ladder is:

1. **Free evidence:** portfolio/risk brief or route plan that gets a user to a real quote.
2. **Paid workflow:** saved policies, recurring analysis, team review, alerts, or richer decision support.
3. **Optional action:** exact-quote approval and bounded execution for users who need it.
4. **Retention:** reconcile outcomes and make the next decision easier, rather than optimizing for one-off prompts.

Track contribution margin instead of assuming “agents” are cheap:

```text
contribution_margin_per_run
  = revenue_attributed_to_run
  - model_cost
  - Suwappu_API_cost
  - infrastructure_cost
  - expected_support_and_loss_budget
```

See [Build a paid CrewAI product on Suwappu](docs/BUILD_A_CREW_PRODUCT.md) for product ladders, instrumentation, and launch gates.

## Project layout

- `src/crew.py` — sequential crew, structured `TradePlan`, CLI, deterministic execution command
- `src/runtime.py` — bounded Suwappu operations, typed failures, metadata-only API events
- `src/agents/` — bounded analyst, risk reviewer, and trade planner
- `src/tools/suwappu_tools.py` — native async CrewAI tools + non-agent execution boundary
- `tests/` — safety and idempotency behavior tests
- `docs/BUILD_A_CREW_PRODUCT.md` — commercialization and production guide
- `docs/OPERATIONS.md` — tenant, observability, retry, release, and incident-response contract
- `examples/` — minimal invocation example

The repo intentionally defines the safety-critical wiring in Python. CrewAI's current JSON-first and classic YAML configuration systems are both useful, but hiding the execution boundary in a config file would make this financial example harder to audit.

## Development

```bash
python -m pip install -e ".[dev]"
python -m ruff check src tests
python -m ruff format --check src tests
python -m compileall -q src tests
python -m pytest -q
python -m pip check
python -m pip_audit --local --ignore-vuln PYSEC-2026-311
python -m build
```

CI runs lint/format/compile/package/behavior gates on Python 3.10 and 3.13, audits dependencies, and clean-installs the built wheel. `PYSEC-2026-311` is the one scoped audit exception: CrewAI 1.15.12 installs a ChromaDB version affected by [CVE-2026-45829](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c), but this product never starts/exposes the vulnerable Chroma HTTP server and keeps Crew memory disabled. [SECURITY.md](SECURITY.md) defines when that exception is invalid.

## Hosted MCP alternative

CrewAI can also consume MCP servers. If you want Suwappu's broader agent tool surface rather than a small SDK allowlist, connect to:

```text
https://api.suwappu.bot/mcp
```

Use the SDK pattern here when you want the host application to own a small, explicit capability set. Use MCP when dynamic tool discovery and the broader surface are the better fit.

## Links

- [Suwappu developer docs](https://suwappu.bot/docs)
- [Suwappu Python SDK source](https://github.com/0xSoftBoi/suwappubot/tree/main/packages/sdk-python)
- [CrewAI custom tools](https://docs.crewai.com/en/concepts/tools)
- [CrewAI task outputs](https://docs.crewai.com/en/concepts/tasks)
- [CrewAI Flows](https://docs.crewai.com/en/concepts/flows)
- [CrewAI tracing](https://docs.crewai.com/en/observability/tracing)

## License

[MIT](LICENSE)
