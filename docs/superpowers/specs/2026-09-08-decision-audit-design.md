# Decision Audit — Design

**Date:** 2026-09-08
**Status:** Design approved, not yet planned or implemented
**Applies to:** every decision point in the request path — routing,
classification, security verdicts, bundle composition, cache, model access,
escalation, budget

## Problem

WaddleAI makes many decisions per request and records almost none of them in a
way that can be audited afterwards. When a decision goes wrong, the failure is
usually invisible:

- **Bug 7** — the classifier requested a withdrawn model, degraded to its safe
  default, and every request routed identically. No error, no counter, no log.
- **Bug 8** — a thinking model returned an empty string; same silent
  degradation, different cause. Found by accident while benchmarking.
- The security auditor allowed ransomware and credential-dumping prompts in
  measured testing. Nothing recorded that a verdict had been reached, let alone
  what it was.

Each subsystem currently decides for itself what to log. Some write a DB trace,
some log at INFO, some do nothing. There is no way to ask "why did this request
get this treatment?" and get one answer.

**Decisions are also nested.** Classification feeds routing; bundle composition
feeds the security verdict; a cache hit skips work downstream. Auditing a single
decision in isolation cannot explain an outcome — the tree is the unit.

## Decisions

| Question | Decision |
|---|---|
| Scope | **Every decision point**, not just routing |
| Structure | A **common envelope** every decision conforms to |
| Correlation | `request_id` across all decisions; OTel spans give the tree |
| Signals | Span + metric + durable log, per the routing design's split |
| Cardinality | Free text never becomes a metric label |

## The decision envelope

Every decision point emits the same shape, so a reader who understands one
understands all of them and a query can span decision types:

| Field | Meaning |
|---|---|
| `decision_point` | `classify`, `route`, `security_verdict`, `bundle_compose`, `cache_lookup`, `model_access`, `escalate`, `budget` |
| `request_id` | Correlates the whole tree |
| `inputs` | What the decision saw — the summarised, non-PII form |
| `options` | The candidate set considered, where there is one |
| `chosen` | What it selected, or the verdict reached |
| `source` | What produced it: `explicit`, `heuristic`, `model`, `policy`, `default` |
| `reason` | Free text where a model decided; a rule id where a rule did |
| `degraded` | **Whether a fallback or safe default was used** |
| `duration_ms` | How long it took |

**`degraded` is the field that matters most.** Every bug this session shared one
property: a component fell back to a safe default and nothing recorded it. A
boolean on every decision makes silent degradation countable, and therefore
alertable, without anyone having to anticipate the specific failure.

## The tree

Decision spans nest under the request span, so the path is reconstructable
without joining anything:

```
request  a1b2c3
├─ classify          tool_type=code-gen complexity=4  source=model     degraded=false
├─ bundle_compose    effective=[security-attack, pii-basic]            degraded=false
├─ security_verdict  block=false  source=model  guard=granite3-guardian
├─ cache_lookup      hit=false                                          degraded=false
└─ route             model=gemma4:12b-it-qat  source=weighted          degraded=false
   └─ escalate       triggered=false
```

A degraded decision anywhere is visible at a glance, and its position shows what
downstream work ran on a bad input.

## Signals

Same three-way split as the routing design, for the same reasons:

- **Span** per decision, nested — carries the full envelope including `reason`
- **Metric** — `waddleai.decisions` (counter) and `waddleai.decision.duration`
  (histogram), labelled by `decision_point`, `source`, `degraded`, `outcome`.
  Bounded label set only.
- **Log** — one structured record per decision carrying the high-cardinality
  detail

**`waddleai.decisions{degraded="true"}` is the single most valuable series this
design produces.** Alert on it and every silent-degradation bug in this
session's list becomes a page rather than an archaeology exercise.

## What must never be a metric label

`reason` (unbounded free text) · `request_id` · `org_id` / `user_id` (unbounded
tenant and user counts) · model-generated tags before vocabulary normalisation.

Those belong in the span and the log. A metric label set must stay bounded by
construction, not by convention.

## PII

Identifiers in any signal are UUIDs only, never email or username, per the PII
tokenisation rule. `inputs` carries a **summarised, non-PII** form — a prompt
hash and length, not the prompt. A security verdict records the categories that
matched, not the offending text.

This matters more here than elsewhere: an audit log is exactly the artefact
most likely to be exported, retained long-term, and read by people outside the
original request's trust boundary.

## Durability and licensing

Operational telemetry is sampled and short-lived by nature. Some decisions —
security verdicts, model-access rejections, bypass grants — are compliance
evidence and need durable retention.

Durable audit records are an **Enterprise-tier** feature per the tier table's
"audit & compliance (audit logs)". The span and metric emission are not gated:
every deployment gets observability, and Enterprise adds durable, exportable
retention. Safety and debuggability are not the upsell.

## Error handling

| Condition | Behaviour |
|---|---|
| Emission fails (collector down) | Never blocks the request; drop and count locally |
| A decision point raises before deciding | Emit with `degraded=true` and the exception class as `reason` |
| Sampling drops a span | The metric still increments — aggregate counts stay correct |

## Testing

- **Envelope conformance** — every decision point emits all required fields. A
  point that emits nothing is the failure this design exists to prevent, so the
  test enumerates decision points rather than asserting per-site.
- **`degraded` correctness** — force each known degradation path (unreachable
  classifier, empty model response, no candidates, guard timeout) and assert the
  flag is set. This is the direct regression test for bugs 7 and 8.
- **Cardinality guard** — assert `reason`, `request_id` and `org_id` are absent
  from metric labels.
- **Tree completeness** — one request produces one connected span tree with no
  orphans.
- **PII absence** — no raw prompt text or user identifier in any emitted signal.

## Out of scope

- Retention policy and export format for durable audit records
- A UI for browsing decision trees (the data comes first)
