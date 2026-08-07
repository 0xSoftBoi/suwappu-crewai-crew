# Security Policy

This repository is a standalone CrewAI integration built on the [Suwappu API](https://github.com/0xSoftBoi/suwappubot). Treat API keys, wallet credentials, approval records, execution identifiers, model traces, and customer prompts as sensitive.

## Reporting a vulnerability

Do not open a public issue for security reports. Use GitHub Private Vulnerability Reporting when enabled, or email **security@suwappu.bot**. Include the affected file/version, reproduction steps, and impact assessment.

Issues in the Suwappu API, shared SDKs, contracts, or custody/key-management layer should be reported through the [core security policy](https://github.com/0xSoftBoi/suwappubot/security/policy).

## Execution boundary

CrewAI agents in this repo do not receive a live managed-wallet execution tool. Managed submission is a separate host function that requires all of the following:

- an exact `quote_id` approved outside the model loop;
- a persisted `approved_intent_id` used as Suwappu's idempotency key;
- `SUWAPPU_ALLOW_MANAGED_EXECUTION=1`; and
- a fresh simulation against the agent's managed wallet that reports `would_execute`.

Do not weaken this boundary by exposing `execute_approved_managed_swap()` as a general-purpose model tool.

A timeout/network failure, HTTP 408/5xx, or malformed successful response during submission can leave the result unknown. The host converts those cases to `ManagedExecutionOutcomeUnknown`. Reconcile managed swap status/history before retrying, and reuse the same intent ID for the same intended economic action.

## Operational guidance

- Keep secrets out of prompts, traces, logs, committed files, and issue reports.
- Keep CrewAI cache, memory, and crew sharing disabled unless the replacement design has an explicit tenant-isolation and retention review.
- Use wallet policies and application-level limits appropriate to the product.
- Prefer read/quote/simulate/prepare paths until a live boundary is explicitly required.
- Test failure, timeout, and reconciliation behavior before funding a managed wallet.
- Never describe a quote, simulation, or unsigned transaction as an executed trade.

The `suwappu_crewai.api` logger is intentionally metadata-only. Do not add tool arguments, response bodies, wallets, quote/swap IDs, credentials, or exception messages to that event stream.

## Known transitive advisory

CrewAI 1.15.12 installs ChromaDB 1.1.x. GitHub's reviewed [CVE-2026-45829 advisory](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c) reports a critical pre-authentication code-injection issue in the ChromaDB HTTP server and currently lists no patched version.

This product does **not** start or expose a Chroma HTTP server and explicitly creates the financial Crew with `memory=False`, `cache=False`, and `share_crew=False`. CI therefore carries one narrow `pip-audit` exception for `PYSEC-2026-311`; every other auditable dependency advisory remains blocking.

The exception is invalid if a deployment enables Crew memory, launches or exposes Chroma's server/API, or otherwise makes the affected server path reachable. In that case, do not ship with this waiver. Re-evaluate the exception on each CrewAI/Chroma update and remove it as soon as a supported fixed dependency is available.

See [docs/OPERATIONS.md](docs/OPERATIONS.md) for the retry matrix, multi-tenant boundary, deployment gates, and live-money incident runbook.

## Our commitment

We aim to acknowledge reports within 3 business days and triage severity within 7 business days. Good-faith research under this policy, without privacy violations, data destruction, or service degradation, is covered by our safe-harbor intent.

