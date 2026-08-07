# Changelog

All notable changes to the standalone CrewAI integration are recorded here.

## 2.1.0 - Unreleased

- Add a bounded, metadata-only observable runtime around every Suwappu SDK operation.
- Add typed transport and protocol failures without logging prompts, tool arguments, credentials, wallets, or response bodies.
- Treat HTTP 408, 5xx, transport timeouts/failures, and malformed managed-execution successes as outcome-unknown.
- Validate quote and managed-execution identifiers before presenting them as usable results.
- Explicitly disable CrewAI cache, memory, and crew sharing in the financial planning path.
- Add an operations/runbook guide, dependency auditing, Ruff gates, Dependabot, and a clean wheel-install contract.

## 2.0.0 - 2026-08-07

- Upgrade to CrewAI 1.15.x native async tools and structured Pydantic output.
- Remove managed execution from the model tool surface.
- Add the deterministic exact-quote host execution path with durable idempotency.
- Add same-chain/cross-chain quoting, simulation, unsigned transaction preparation, wallet discovery, and swap-history reconciliation.
- Add the paid-product builder guide and Python 3.10/3.13 behavioral CI.
