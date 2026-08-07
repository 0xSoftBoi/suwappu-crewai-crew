# Build a paid CrewAI product on Suwappu

The business opportunity is not “three agents talk to each other.” It is a workflow that takes a user from a costly decision to verified evidence, an explicit approval, and a reconciled outcome.

## 1. Decide whether you need a crew

Start with one model. Add a role only when it creates a measurable benefit.

| Product need | Good shape |
|---|---|
| One narrow quote or portfolio question | Single agent or MCP client |
| Evidence + independent risk challenge + exact trade plan | This three-agent crew |
| Long-running workflow with branching, persistence, or human feedback | CrewAI Flow around a crew |
| Deterministic API operation | Normal application code, not another agent |

CrewAI's current architecture distinguishes autonomous Crews from more controlled, event-driven Flows. For financial actions, keep the irreversible edge deterministic even if a Crew or Flow produces the proposal.

## 2. Use a trust-boundary architecture

The reference implementation has three authority levels:

1. **Read:** prices, portfolio, chains, tokens, managed-wallet addresses, swap history.
2. **Prepare:** quote, simulate, and build an unsigned self-custody transaction.
3. **Submit:** deterministic host code executes one exact managed-wallet quote with a persisted idempotency key.

Do not give a model more authority just because it produced a convincing explanation. Prompt text is not an authorization system.

For managed execution, persist at least:

- internal user/account id;
- intent id / idempotency key;
- approved quote id;
- approval actor and timestamp;
- requested asset/amount/chain constraints;
- returned Suwappu swap id;
- terminal outcome after status or webhook reconciliation.

Keep the product intent ledger separate from the chain/execution ledger. A timeout is not proof that nothing happened.

## 3. Pick a product people pay for

### Portfolio decision desk

Free: a one-time evidence-backed portfolio/risk brief. Paid: saved allocation policies, comparison history, recurring reviews, exports, or team approval. Optional action: exact-quote execution after approval.

### Treasury copilot

Analyst collects current state, risk reviewer enforces the organization's constraints, and planner produces a structured candidate. Charge for workflow seats, governance, auditability, and time saved rather than promising trading returns.

### Embedded route assistant

Give another product a branded “explain and prepare” experience. The client application owns identity and approval; Suwappu provides the quote/execution surface. Monetize the application layer only where your commercial and regulatory model permits it.

### Research-to-action workspace

Sell a decision record: current evidence, assumptions, risk challenge, exact route, simulation, approval, and reconciled result. This is often easier to justify than charging for raw model prose.

None of these models guarantees profitability or investment performance. Financial, custody, payments, and advisory rules vary by jurisdiction; design the commercial model with appropriate legal review.

## 4. Make the economics explicit

A multi-agent run can make several model calls before a user reaches a quote. Measure the full cost path.

```text
contribution_margin_per_run
  = attributed_revenue
  - analyst_model_cost
  - risk_model_cost
  - planner_model_cost
  - Suwappu_API_usage
  - infrastructure
  - expected_support_and_loss_budget
```

This repo caps each agent at `max_iter=6`; that is a ceiling, not a cost forecast. Capture actual model usage and tool calls in your application. If the risk-review step does not change decisions or improve retention, remove it.

Useful pricing experiments include a subscription for recurring workflows, workspace/seat pricing for teams, or usage tiers tied to application value. Do not hard-code a pricing story until you can connect it to retained users and real costs.

## 5. Instrument the acquisition-to-retention loop

Give each product run a stable application ID and connect these events:

```text
docs_or_referral
  -> first_crew_run
  -> first_real_quote
  -> successful_simulation
  -> explicit_approval
  -> managed_submission_or_self_custody_handoff
  -> reconciled_outcome
  -> retained_use
```

Track attention metrics separately from product value. For a developer product, a docs visit is not success; a first valid quote or retained API use is much closer.

At minimum record model/tool cost, latency, quote/simulation success, approval conversion, execution outcome, and repeat usage. Never publish fabricated route savings, revenue, volume, or win-rate claims.

## 6. Production gates

Before managed execution is available to a customer:

- bind quotes to the wallet that will simulate/execute them;
- keep live execution outside the CrewAI tool allowlist;
- persist one durable idempotency key per intended trade;
- reject failed simulations before submission;
- configure server-side wallet policies appropriate to the product;
- treat network/5xx submission failures as potentially unknown outcomes;
- reconcile with swap status/history or signed webhooks before retrying;
- keep secrets out of prompts, logs, traces, and repository history;
- add rate, spend, and model-cost budgets around the workflow;
- test the failure path, not only the happy path.

## 7. SDK versus MCP

Use the Python SDK when you want a small, code-reviewed capability surface like this repo. Use Suwappu's hosted MCP endpoint when a CrewAI deployment should discover the broader tool set without hand-wrapping every capability.

Hosted endpoint:

```text
https://api.suwappu.bot/mcp
```

Either way, keep financial authorization in the host. Tool discovery does not change the approval model.

## 8. Ship the smallest measurable loop

A good first product milestone is not autonomous trading. It is:

1. one user can reach a valid wallet-bound quote;
2. the product can explain the evidence and risk in structured form;
3. the user can approve one exact quote;
4. the system submits idempotently and reconciles the outcome; and
5. you can measure whether that user comes back.

Once that loop is reliable and retained, add automation deliberately.

