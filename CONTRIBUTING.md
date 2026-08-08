# Contributing

Thanks for improving the Suwappu CrewAI integration. The agent/runtime split is a security boundary, not an implementation detail.

## Local release gate

Use a supported Python version (3.10 through 3.13) in an isolated environment:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pip check
python -m ruff check src tests
python -m ruff format --check src tests
python -m compileall -q src tests
python -m pytest -q
python -m pip_audit --local --ignore-vuln PYSEC-2026-311
```

The single audit exception is scoped and documented in [SECURITY.md](SECURITY.md). Do not broaden it or add another waiver without a written reachability/mitigation analysis and removal condition.

## Authority invariants

Changes must preserve these rules:

- Managed execution stays outside the CrewAI/model tool surface. Do not expose `execute_approved_managed_swap()` as a general agent tool.
- Host execution requires the exact approved quote, persisted approved intent ID, explicit `SUWAPPU_ALLOW_MANAGED_EXECUTION=1`, and a fresh simulation that reports `would_execute`.
- The approved intent ID is the durable idempotency key for that economic action.
- Timeout/network failures, HTTP 408/5xx, and malformed successful execution responses are outcome-unknown. Reconcile status/history before retrying with the same intent ID.
- Crew cache, memory, and sharing stay disabled for the financial path unless a replacement has an explicit tenant-isolation and retention review.
- API telemetry remains metadata-only. Do not add prompts, tool arguments, credentials, wallets, response bodies, quote/swap identifiers, or exception messages.

A new CrewAI tool needs an explicit authority class, bounded runtime behavior, typed failure semantics, tests, and README/operations documentation in the same change.

## Pull requests

Keep changes narrow. Before merge:

- run the local release gate above;
- test both the success path and relevant authority/failure paths;
- update the changelog for externally meaningful behavior;
- document migrations for CLI/schema/default/authority changes; and
- keep secrets and customer data out of code, fixtures, traces, issues, and review comments.

CI additionally builds both wheel and source distribution, clean-installs the wheel, exercises Python 3.10/3.13, audits dependencies, and runs CodeQL.

Security-sensitive findings should follow [SECURITY.md](SECURITY.md), not a public issue.
