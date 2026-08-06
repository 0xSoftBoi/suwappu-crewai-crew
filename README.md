# suwappu-crewai-crew

A safe-by-default multi-agent [CrewAI](https://crewai.com) example built on [Suwappu](https://suwappu.bot).

Three agents collaborate on market analysis, risk review, and trade planning. The default crew can quote and simulate, but **cannot call managed-wallet execution**. Live execution requires two deliberate host-side controls: the `--execute` flag and `SUWAPPU_ALLOW_MANAGED_EXECUTION=1`.

## Current SDK status

The Python SDK in `0xSoftBoi/suwappubot/packages/sdk-python` is currently source-only; it is not yet published on PyPI. This repository therefore pins that package to a specific `suwappubot` commit in `pyproject.toml` so a clean checkout is installable and reproducible.

When `suwappu` is published to PyPI, replace the pinned VCS dependency with the released version.

## Quick start

```bash
git clone https://github.com/0xSoftBoi/suwappu-crewai-crew.git
cd suwappu-crewai-crew

python -m venv .venv
source .venv/bin/activate
python -m pip install -e .

export SUWAPPU_API_KEY=suwappu_sk_...
export OPENAI_API_KEY=sk-...

# Safe default: analyze, quote, and simulate only.
suwappu-crew "Analyze ETH on Base and Arbitrum and propose a trade plan"
```

Register a Suwappu agent if you do not have an API key yet:

```bash
curl -X POST https://api.suwappu.bot/v1/agent/register \
  -H "Content-Type: application/json" \
  -d '{"name":"my-crewai-agent"}'
```

## Agent roles

| Agent | Tools | Can move funds by default? |
|---|---|---:|
| Market Analyst | prices, chains, tokens, portfolio | No |
| Risk Manager | prices, portfolio | No |
| Trade Planner | quote, simulate | No |
| Trade Executor (opt-in mode) | quote, simulate, managed execute | **Yes** |

Portfolio lookups require a wallet address. Simulation requires both a `quote_id` and wallet address.

## Live managed-wallet execution

Prompt text is not an approval boundary. To expose the live tool, the host has to opt in twice:

```bash
export SUWAPPU_ALLOW_MANAGED_EXECUTION=1
suwappu-crew --execute "Execute the already-approved ETH to USDC plan on Base"
```

`--execute` changes the trader's tool allowlist for that run. Without it, the execution tool is not present. The environment guard is a second defense if somebody imports the tool directly.

Before live use, provision the agent's managed wallet and configure appropriate Suwappu wallet policies. Do not use a model prompt as a substitute for application-level approval or server-side limits.

## Suwappu tools

| CrewAI tool | Current SDK call | Behavior |
|---|---|---|
| Get token prices | `client.get_prices(symbols, chain)` | Read-only |
| Get swap quote | `client.get_quote(...)` | Read-only quote |
| Simulate swap | `client.simulate_swap(...)` | Dry-run, no broadcast |
| Get portfolio | `client.get_portfolio(wallet_address, chain)` | Read-only |
| List chains | `client.list_chains()` | Read-only |
| List tokens | `client.list_tokens(chain)` | Read-only |
| Execute managed swap | `client.execute_swap(quote_id)` | **Live; opt-in** |

Tool results are JSON strings so CrewAI receives structured, machine-readable output instead of Python object representations.

## Examples

```bash
# Analysis
suwappu-crew "Compare ETH and SOL prices and explain the route choices"

# Portfolio review — provide the wallet address in the request
suwappu-crew "Review wallet 0x... on Base and suggest a lower-risk allocation"

# Quote/simulation plan, still no live execution
suwappu-crew "Quote 100 USDC to ETH on Base and simulate it for wallet 0x..."
```

## Execution model

The current Python SDK's `execute_swap()` uses Suwappu's managed-wallet pipeline at `POST /v1/agent/swap/execute`. A successful submission returns a Suwappu swap id/status and may also return a transaction hash or polling URL.

This differs from self-custody transaction preparation. Do not describe a managed execution result as an unsigned transaction, and do not describe a quote or simulation as an executed trade.

## Project layout

- `src/crew.py` — CLI, task orchestration, and execution-mode gate
- `src/agents/` — analyst, risk manager, and trader definitions
- `src/tools/suwappu_tools.py` — CrewAI wrappers around the current Python SDK
- `src/config/` — reference YAML for agent/task customization
- `examples/` — simple invocation example

The runtime currently constructs agents/tasks in Python; the YAML files are reference templates rather than automatically loaded configuration.

## Development

```bash
python -m pip install -e .
python -m compileall -q src
python -c "from src.crew import sanitize_query; assert sanitize_query('Analyze ETH') == 'Analyze ETH'"
```

CI runs the editable install, source compilation, and import smoke test as blocking checks.

## Hosted MCP alternative

If your CrewAI stack can consume MCP and you want the broader Suwappu tool surface (predictions, perps, lending, swap status/history, wallet policies, and more), use the hosted MCP endpoint:

```text
https://api.suwappu.bot/mcp
```

## Links

- [Suwappu docs](https://docs.suwappu.bot)
- [Python SDK source](https://github.com/0xSoftBoi/suwappubot/tree/main/packages/sdk-python)
- [Hosted MCP](https://api.suwappu.bot/mcp)

## License

[MIT](LICENSE)
