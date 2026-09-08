# Model Inventory and Weighted Selection — Design

**Date:** 2026-09-08
**Status:** Design approved, not yet planned or implemented
**Related, deliberately independent:** classifier bundles
(`2026-09-08-classifier-bundles-design.md`), tool-type vocabulary
(`2026-09-08-tool-type-vocabulary-design.md`, amended by this document)

## Problem

Three separate defects share one root cause: **which model serves which job is
decided in too many places, and the database is not one of them.**

1. **The DB rows exist and nothing reads them.** `model_assignments` carries
   seeded rows for WaddleAI's internal functions (`routing-classifier`,
   `security-audit`, `summarize`, `docs-fetch`, `embeddings`). The engine
   resolves assignments for ordinary request tool types, but **never for these**.
   `security-audit` is read from `SECURITY_AUDITOR_MODEL` or a hardcoded
   default; the classifier model comes from a constant in `tool_type.py`, since
   the engine never passes one. The WebUI's "Routing LLM Model" selector writes
   a row that nothing consults — the API returns 200, the UI shows the new
   value, and the running classifier ignores it.

2. **Nothing validates that a configured model exists.** Bug 7 (2026-09-08) had
   the classifier requesting the withdrawn `gemma4:e2b` from a host that did not
   have it. The call 404'd, `classify()` degraded to its safe default, and every
   request routed identically with no error anywhere.

3. **A rigid tool_type → model table cannot express model quality.** A model is
   not simply "the code model"; it is strong at some work and weak at other
   work, and that profile is what should drive selection.

## Decisions

| Question | Decision |
|---|---|
| Who installs/removes models | **Global admin** — the inventory |
| Who disables models and bundles | **Tenant admin** — narrowing within what is installed |
| Caller override | The existing header, naming an exact model and provider |
| Internal-function roles | **Explicit model, deterministic** — no weighting |
| Request routing | **Weighted** — the router receives metadata and chooses |
| Where model config lives | **The database**, not container env vars |
| Model existence | **Validated against the target server** |

## Two selection mechanisms, deliberately different

**Explicit, for roles where ambiguity is a liability:**

`security-audit` · `embeddings` · `summarize` · `docs-fetch`

An operator names the model. "Which guard judged this request" must have exactly
one answer, and an embedding model cannot vary per request at all — its choice
is baked into stored vectors (see the classifier-bundles design).

**Weighted, for request routing:**

The routing model receives the candidate models with their capability metadata
and **makes the call itself**. There is no `tool_type → model` lookup for
request traffic.

```
classifier output ──┐
  tool_type: code-gen                    ┌─> routing model picks
  complexity: 4      ├─ as context ──────┤     gemma4:12b-it-qat
  needs_reasoning: true                  └─>  + stated reason
                    │
model capability weights ──┘
  gemma4:12b-it-qat   coding 0.9  conversation 0.4  research 0.3
  claude-sonnet       coding 0.8  conversation 0.9  research 0.9
  gemma4:e4b          coding 0.2  conversation 0.6  research 0.5
```

Both `tool_type` and the weights are **metadata fed to the router**. Neither is
a join key.

## The three-level narrowing model

Model availability narrows at each level. This is the mirror image of classifier
bundles, which are additive-only — and deliberately so: bundles add protection,
models restrict choice.

```
global admin      installs / uninstalls        what exists at all
      ∩
tenant admin      disables                     what this tenant permits
      ∩
caller header     names one exactly            what this request uses
```

**Determinism falls out of this for free.** A tenant that wants one model per
job disables the others; the router then has one candidate and no discretion. No
separate pinning mechanism is needed, and a compliance requirement is expressed
with the same control as an ordinary preference.

A caller's header selects **within** what the tenant permits. A header naming a
disabled or uninstalled model is an error, not a silent fallback — see below.

## Architecture

### Inventory

`model_registry` (migration 008) gains the capability profile and deployment
association:

- `capabilities` (JSON) — weights per dimension, e.g.
  `{"coding": 0.9, "conversation": 0.4, "research": 0.3, "reasoning": 0.7}`.
  Hand-authored by a global admin at install time; this is a curated judgement,
  not a benchmark output.
- `served_by` — which fleet backend / deployment offers it.
- `installed_at`, `installed_by`, `last_validated_at`.

`model_tenant_state` — `org_id`, `model_id`, `enabled`, `updated_by`,
`updated_at`. A tenant admin's disable list, with an audit trail. Absence means
enabled: a newly installed model is available to every tenant until a tenant
turns it off.

### Existence validation

**A model is not installable until it is confirmed present on its target
server.** At install, and on a schedule thereafter, the platform queries the
backend (for Ollama, `/api/tags`) and records `last_validated_at`.

A model that fails validation is marked unavailable and excluded from routing
candidates, with an operator-visible warning. This is the direct fix for bug 7:
requesting a model the host does not have becomes a loud inventory error rather
than a silent routing degradation.

### Wiring the internal-function rows

`routing-classifier`, `security-audit`, `summarize` and `docs-fetch` resolve
from `model_assignments` at runtime. The corresponding environment variables
(`SECURITY_AUDITOR_MODEL`, `SUMMARIZE_MODEL`) become a bootstrap default only —
consulted when no row exists — and the resolved value is reported in the trace
so an operator can see which source won.

This makes the existing WebUI selector honest. Today it writes a row nothing
reads.

### Routing trace

Weighted selection is **non-deterministic**: the same request may route
differently between two calls. That is acceptable for quality and unacceptable
for debugging unless the inputs are recorded, so `routing_decision_traces` must
capture, in addition to the chosen model:

- the candidate set after global/tenant narrowing
- the capability weights the router was shown
- the classifier output (`tool_type`, complexity, needs_reasoning)
- the router's **stated reason** for its choice

Recording only the decision makes a bad route unreproducible. Recording the
inputs makes it explicable.

### OpenTelemetry emission

Every routing decision emits **three signals**, split by what each is good at.
The split is not stylistic — putting the wrong field in the wrong signal breaks
the backend.

**Span** (`waddleai.routing.decide`) — one per decision, on the existing tracer
in `shared/observability/tracing.py`. Carries the full picture as attributes:

| Attribute | Example |
|---|---|
| `waddleai.route.model` | `gemma4:12b-it-qat` |
| `waddleai.route.provider` | `ollama` |
| `waddleai.route.tool_type` | `code-gen` |
| `waddleai.route.complexity` | `4` |
| `waddleai.route.source` | `weighted` \| `explicit` \| `caller_header` |
| `waddleai.route.candidates` | `["gemma4:12b-it-qat", "claude-sonnet"]` |
| `waddleai.route.weights` | the profile the router was shown |
| `waddleai.route.reason` | the router's stated reason, free text |
| `waddleai.route.narrowed_by` | `tenant_disabled` \| `not_installed` \| `none` |

**Metric** — counters and a histogram, for aggregation and alerting:

- `waddleai.routing.decisions` (counter) — labels: `model`, `tool_type`,
  `source`, `outcome`
- `waddleai.routing.duration` (histogram) — how long the decision took,
  including any classifier call
- `waddleai.routing.degraded` (counter) — labels: `cause`
  (`classifier_empty`, `classifier_error`, `no_candidates`,
  `model_unavailable`). **This is the counter that would have made bugs 7 and 8
  visible on day one** rather than surfacing as "the router returns a constant".

**Log** — one structured record per decision, carrying the high-cardinality
detail a metric cannot hold: `request_id`, the reason text, the full weight set.

**The cardinality rule is load-bearing.** The router's free-text reason must
**never** be a metric label — it is unbounded, and one such label will blow up
any metrics backend. Reason text belongs in the span and the log. Metric labels
stay to a bounded set: model name, tool type, source, outcome, degradation
cause.

**PII:** identifiers in telemetry are UUIDs only, never email or username, per
the PII-tokenisation rule. `org_id` is acceptable as a span attribute and a log
field; it is **not** a metric label — tenant count is unbounded and would
multiply every series.

**Open question for implementation, not settled here:** metrics today are
`prometheus_client` (`shared/utils/metrics.py`), while tracing is OTel. Emitting
OTel metrics means either running two metric stacks or bridging one to the
other (OTel ships a Prometheus exporter). Pick deliberately; do not let a second
stack appear by accident.

**Relationship to `routing_decision_traces`.** The DB table stays the durable,
queryable corpus — it is what an operator greps months later and what the
aggregate WebUI reads. OTel is the operational path: live dashboards, alerting,
and correlation with the surrounding request span. They carry overlapping
content on purpose and answer different questions.

## Amendment to the tool-type vocabulary design

That document argues for a closed, kebab-case `tool_type` vocabulary **because
it was an exact-match join key** against `model_assignments`. Under weighted
selection it is not a join key for request routing — it is context a language
model reads, and a router shown `code_refactoring` understands it perfectly.

The vocabulary work therefore **drops in priority and changes in character**:

- Still worth having for consistency, observability, and grouping traces
- Still the right shape for the **explicit** internal-function roles, which
  remain exact-match lookups
- **No longer load-bearing** for request routing, and an out-of-vocabulary tag
  is no longer a routing failure

The kebab-case standard stands as a convention. The closed-vocabulary
requirement relaxes to a preference for request traffic.

## Error handling

| Condition | Behaviour |
|---|---|
| Header names an uninstalled model | 400 — never a silent fallback |
| Header names a tenant-disabled model | 403, naming the tenant restriction |
| Tenant disables every candidate for a request | Explicit error; no implicit re-enable |
| Model fails existence validation | Excluded from candidates, operator warning, trace records the exclusion |
| Router returns a model outside the candidate set | Rejected; fall back to the highest-weighted candidate and record the violation |
| No capability weights on a model | Selectable, but ranked last — an unprofiled model is not silently preferred |

## Testing

- **Narrowing property test** — for any (global, tenant, caller) combination the
  effective candidate set is a subset of what is installed and never re-widens.
  The mirror of the bundles composition test, and the security-critical
  invariant here.
- **Existence validation** — a configured-but-absent model is excluded and
  warned about rather than attempted. This is the bug 7 regression test.
- **Router containment** — a router naming a model outside the candidate set
  does not escape the narrowing.
- **Trace completeness** — every decision records candidates, weights, classifier
  output and reason. Asserting only that a model was chosen would let the
  debugging story rot silently.
- **Telemetry emission** — a decision emits its span, metric and log, and the
  degradation counter increments on a degraded route. That counter is the
  regression test for bugs 7 and 8: both were silent precisely because nothing
  counted a fallback to the safe default.
- **Metric cardinality** — assert the reason text is NOT among the metric
  labels. Easy to add later "just for debugging" and expensive to discover in
  production.
- **Determinism via narrowing** — with one candidate enabled, N runs of the same
  request all select it.
- **Distribution, not equality** — with several candidates, routing tests assert
  a distribution over repeated runs rather than a single expected model.
  Non-determinism makes exact-match routing assertions flaky by construction.

## Out of scope

- Automatic derivation of capability weights (hand-authored by a global admin)
- Classifier bundles (separate design; bundles and models stay independent)
- Cross-provider cost optimisation
