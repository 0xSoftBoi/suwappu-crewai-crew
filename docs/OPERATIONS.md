# Operating the Suwappu CrewAI product

This is the production control-plane contract for the standalone CrewAI integration. It complements the product design guide; it does not turn an LLM prompt into an authorization system.

## Service boundary

The three CrewAI roles can observe, quote, simulate, prepare unsigned transactions, and produce a structured plan. They cannot broadcast a managed swap. Live managed execution stays in deterministic host code and accepts one exact pre-approved quote plus one durable intent ID.

For a service deployment, keep four concerns separate:

1. **Identity and tenant policy** — your authenticated application.
2. **Agent reasoning** — CrewAI with the non-broadcasting tool allowlist.
3. **Economic intent** — a durable database record owned by the host.
4. **Execution/reconciliation** — deterministic code plus Suwappu status/history or signed webhooks.

CrewAI Flow persistence can be useful for long-running workflow state, but it is not a replacement for the economic intent ledger. CrewAI's official Flow APIs also support human-feedback checkpoints. Use those for workflow UX if useful; keep the final money-moving authorization enforceable outside model text.

## Runtime request contract

Every SDK operation passes through `src.runtime.call_suwappu()`.

- The shared Python SDK has a 30-second HTTP deadline.
- This product adds a 25-second operation deadline by default.
- Override it with `SUWAPPU_OPERATION_TIMEOUT_SECONDS` from `0.01` through `30`.
- A timeout cancels the local await. It does **not** prove a managed-execution request was never accepted by the server.

The `suwappu_crewai.api` logger emits one metadata-only event per Suwappu operation:

~~~json
{
  "operation": "get_quote",
  "outcome": "success",
  "duration_ms": 142.3
}
~~~

HTTP errors add only the status. Events never include prompts, tool arguments, API keys, wallet addresses, quote/swap IDs, request/response bodies, or exception messages. Add tenant/run correlation in your own logging context; do not turn customer identifiers into high-cardinality metric labels.

## Failure classes and retries

| Operation/result | Retry rule |
|---|---|
| Discovery, portfolio, prices, history read | A bounded retry is reasonable for transient transport/5xx errors if the calling product can tolerate staleness |
| Quote | Get a fresh quote; do not retry an expired quote indefinitely |
| Simulation | Retry only as a fresh preflight; a simulation never proves execution |
| Unsigned preparation | Re-prepare from a still-valid/fresh quote as product policy allows |
| Managed execution, known 4xx other than 408 | Treat as a rejected request; fix the cause before another submission |
| Managed execution, timeout/network/408/5xx | **Outcome unknown**; reconcile before any retry |
| Managed execution, malformed successful response | **Outcome unknown**; reconcile before any retry |

Do not add a generic retry decorator around the tool module.

The host raises `ManagedExecutionOutcomeUnknown` with the original approved intent ID available as structured exception state. Store the intent before submission. Reuse the same idempotency key only when reconciliation shows the same intended action still needs submission.

## Durable intent state machine

A useful minimum state model is:

~~~text
proposed -> approved -> submitting -> submitted -> terminal
                              |
                              +-> outcome_unknown -> reconciling -> submitted/terminal
~~~

Persist:

- tenant/account ID;
- intent/idempotency key with a uniqueness constraint;
- exact approved quote ID and its policy constraints;
- approval actor, source, and timestamp;
- simulation result/reference used at approval;
- submission attempt timestamps;
- returned swap ID when known;
- last reconciliation source/time;
- terminal status and transaction reference when available.

Do not derive a fresh idempotency key from the current timestamp during a retry.

## Multi-tenancy

The CLI uses one server-side `SUWAPPU_API_KEY`. A multi-tenant SaaS should resolve credentials and policy from its authenticated tenant context instead of placing tenant secrets in prompts.

This repository explicitly creates the Crew with:

- `cache=False` so financial tool output is not reused as if it were fresh;
- `memory=False` so model memory is not an implicit customer-data store;
- `share_crew=False`.

If you turn any of those capabilities on, perform a new tenant-isolation and retention review first.

Apply per-tenant concurrency, request, spend, and model-token budgets. Keep a separate queue/capacity lane for reconciliation so a traffic spike cannot starve the requests needed to determine whether money already moved.

## Tracing and sensitive data

CrewAI's built-in tracing can capture agent decisions, task timelines, tool use, and LLM calls. That is valuable operationally and sensitive by design.

Before enabling CrewAI AMP or another tracing backend:

- decide which prompts/tool arguments may contain wallet or customer data;
- redact or avoid secrets before they enter model context;
- define retention and access controls;
- keep API keys and approval credentials out of trace attributes;
- verify tenant isolation in the tracing backend;
- ensure deletion/export behavior matches your customer contract.

The adapter's own API event logger is deliberately narrower and body-free.

## Dependency security exception

CrewAI 1.15.12 currently depends on ChromaDB 1.1.x. GitHub's reviewed [CVE-2026-45829 advisory](https://github.com/advisories/GHSA-f4j7-r4q5-qw2c) reports a critical pre-authentication code-injection issue in the ChromaDB HTTP server with no patched version listed.

This product does not start or expose a Chroma server and explicitly disables Crew memory. CI therefore ignores only `PYSEC-2026-311` while continuing to fail on every other auditable dependency advisory.

That exception becomes invalid if you enable Crew memory, start Chroma's server/API, expose a Chroma port, or otherwise make the affected server code reachable. Re-evaluate the exception whenever CrewAI/Chroma changes, and remove it as soon as a fixed supported dependency path exists.

## SLOs and alerts

Choose SLOs from your customer promise; do not copy illustrative thresholds as guarantees. At minimum measure:

- crew-run success/latency and model cost;
- Suwappu operation count, outcome, and latency;
- quote/simulation success;
- approval conversion;
- managed submissions by state;
- outcome-unknown and reconciliation backlog age;
- terminal execution success/failure;
- per-tenant queue depth and budget rejection;
- dependency-audit and release-gate status.

Alert on sustained transport/protocol errors, a growing reconciliation backlog, repeated policy denials, cost spikes, and any live submission without a corresponding persisted intent.

## Deployment and rollback

Before promotion:

1. run Ruff, compilation, all behavior tests, and `pip check`;
2. run the dependency audit with the single documented Chroma exception;
3. build the wheel/sdist and clean-install the wheel;
4. run model/tool regression scenarios in a no-funds environment;
5. verify the live tool allowlist still has no managed-execution tool;
6. verify the production host policy/idempotency store against a staging account;
7. canary the non-broadcasting path before enabling managed execution.

Rollback application/model changes independently from economic intents already submitted. Never delete or recreate unknown/submitted intent records just because a deployment rolled back.

## Live-money incident runbook

If submission outcomes become ambiguous:

1. disable new managed submissions at the host boundary;
2. keep read/status/history/webhook reconciliation available;
3. freeze the affected intent rows and preserve original idempotency keys;
4. reconcile each unknown intent before retrying anything;
5. inspect Suwappu request/error metadata and signed webhook history without copying secrets into tickets;
6. restore submissions only after the failure mode is understood and a capped canary passes.

If credentials may be exposed, disable execution first, rotate them through the proper control plane, and then reconcile already-submitted intents.

## What enterprise-ready does not mean

These controls improve operability and fail-safe behavior. They are not a certification, legal opinion, investment-performance claim, custody classification, or guarantee that a model-generated plan is correct. Your deployment still owns identity, authorization, tenant isolation, compliance, incident response, and the commercial promise made to customers.
