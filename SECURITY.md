# Security Policy

This repository is a satellite/reference application built on the [Suwappu API](https://github.com/0xSoftBoi/suwappubot). Treat API keys, wallet credentials, approval records, and execution identifiers as sensitive.

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

A network or server failure during submission can leave the result unknown. Reconcile managed swap status/history before retrying, and reuse the same intent ID for the same intended economic action.

## Operational guidance

- Keep secrets out of prompts, traces, logs, committed files, and issue reports.
- Use wallet policies and application-level limits appropriate to the product.
- Prefer read/quote/simulate/prepare paths until a live boundary is explicitly required.
- Test failure, timeout, and reconciliation behavior before funding a managed wallet.
- Never describe a quote, simulation, or unsigned transaction as an executed trade.

## Our commitment

We aim to acknowledge reports within 3 business days and triage severity within 7 business days. Good-faith research under this policy, without privacy violations, data destruction, or service degradation, is covered by our safe-harbor intent.

