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
- **Metric** — `waddleai.decisions` (counter) and the timing histograms below,
  labelled by `decision_point`, `source`, `degraded`, `outcome`. Bounded label
  set only.
- **Log** — one structured record per decision carrying the high-cardinality
  detail

### Timing

One duration per decision is not enough to answer "why was this slow". Time is
spent in distinct phases with different causes and different fixes, so each gets
its own histogram:

| Metric | Measures | A spike means |
|---|---|---|
| `waddleai.decision.duration` | Time inside the decision itself | The decision logic or its model call is slow |
| `waddleai.model.load_duration` | Cold-loading a model into VRAM | **Eviction thrashing** — see below |
| `waddleai.upstream.prompt_eval_duration` | Upstream processing the prompt | Long contexts, or a compute-bound GPU |
| `waddleai.upstream.eval_duration` | Upstream generating tokens | Bandwidth-bound; scales with model size |
| `waddleai.upstream.total_duration` | Whole upstream call | The caller-visible cost |
| `waddleai.request.duration` | End to end through the pipeline | The number a user actually feels |

Paired counters `waddleai.upstream.prompt_tokens` and
`.completion_tokens` make tokens/sec derivable per model without a second
instrument.

**These are not stopwatch measurements.** Ollama returns `load_duration`,
`prompt_eval_duration`, `eval_duration` and `total_duration` on every response;
emit those rather than timing the call from outside. Wrapping a timer around the
HTTP call measures the network and our own overhead too, and cannot separate
load from prompt from generation at all. Where a provider does not report a
breakdown, emit `total_duration` only and leave the rest unrecorded rather than
inventing a split.

**`model.load_duration` is the metric that makes eviction visible.** A model
being evicted and reloaded costs roughly five seconds before a single token is
produced (measured, 2026-09-08). Without this histogram, thrashing caused by
`OLLAMA_MAX_LOADED_MODELS` looks indistinguishable from "the model is slow" —
the request is late, nothing errors, and every other metric looks normal. With
it, a non-zero load time on a steady-state deployment is an immediate signal
that models are being swapped.

Label these by `model` and `provider`, both bounded. **Not** by `org_id` — the
same unbounded-cardinality rule applies.

Splitting prompt from generation also makes the capacity-versus-throughput
distinction observable in production rather than only on a bench: prompt
evaluation is compute-bound and largely size-independent, generation is
bandwidth-bound and scales with model size. Watching them move separately tells
an operator which resource they have actually run out of.

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

**Every test below must capture real emissions, not inspect definitions.** A
test that imports the metrics module and asserts an instrument exists proves
only that someone declared it — the failure mode this whole design exists to
prevent is a signal that is declared and never emitted. Assert on values that
changed as a result of exercising the code.

The mechanism is available in the pinned SDK (verified against
opentelemetry-sdk 1.44.0):

- `opentelemetry.sdk.metrics.export.InMemoryMetricReader` attached to a test
  `MeterProvider` — read back the actual data points and their attributes
- `opentelemetry.sdk.trace.export.in_memory_span_exporter.InMemorySpanExporter`
  — read back the actual spans and their parent links
- `caplog` for the structured log record

### Required tests

- **Emission, per decision point.** Exercise each decision point and assert a
  metric data point and a span actually appear in the in-memory readers. The
  test **enumerates the decision points** from a single registry rather than
  being written per site, so adding a decision point without telemetry fails the
  suite instead of passing silently.
- **Emission is load-bearing.** For at least one decision point, remove the
  emission and confirm the test fails. A telemetry test that passes with the
  emission deleted is worthless, and that is not hypothetical — three bugs this
  session were masked by tests that could not fail.
- **`degraded` correctness.** Force each known degradation path — unreachable
  classifier, empty model response (the bug 8 shape), no candidates, guard
  timeout — and assert `degraded=true` reaches the counter. Direct regression
  test for bugs 7 and 8.
- **Counter arithmetic.** N requests produce N data points. Off-by-one and
  double-counting are invisible in a presence check.
- **Cardinality guard.** Assert `reason`, `request_id` and `org_id` are absent
  from the attribute set of every emitted metric point. Not from the *declared*
  labels — from what was actually recorded.
- **Timing provenance.** Assert the emitted `eval_duration` equals the value in
  the upstream response, not elapsed wall time. Feed a stub whose reported
  duration differs deliberately from real elapsed time; a stopwatch
  implementation passes a naive test and fails this one.
- **Timing completeness.** A provider reporting no breakdown emits
  `total_duration` only, with the other histograms untouched rather than filled
  with a fabricated split.
- **Tree completeness.** One request produces one connected span tree with no
  orphans — assert every decision span has the request span as an ancestor.
- **PII absence.** No raw prompt text and no user identifier in any emitted
  signal. Feed a request containing a distinctive marker string and assert it
  appears in none of the captured spans, metrics or logs.

## Out of scope

- Retention policy and export format for durable audit records
- A UI for browsing decision trees (the data comes first)
