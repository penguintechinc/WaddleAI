# Tool-Type Vocabulary — Design

**Date:** 2026-09-08
**Status:** Design approved, not yet planned or implemented
**Related, deliberately independent:** classifier bundles
(`2026-09-08-classifier-bundles-design.md`), model inventory (not yet written)

## Problem

Stage-2 classification output essentially never matches a `model_assignments`
row. The classifier runs on every request the heuristics punt on, costs a guard
model call, and its result is discarded — routing falls through to capability
ranking. Verified live against a real Ollama on 2026-09-08.

The classifier itself is not the problem. Given a real model it reads requests
well:

| Prompt | tool_type | complexity | needs_reasoning |
|---|---|---|---|
| "What time zone is UTC+1 in winter?" | `time_zone_lookup` | 2 | false |
| "Refactor this module to an asyncio-native cache..." | `code_refactoring` | 4 | true |

The problem is that nothing constrains or reconciles the vocabulary. Three
dialects coexist:

| Source | Convention | Values |
|---|---|---|
| Assignment seeds (migration 010) | kebab | `security-audit`, `routing-classifier`, `embeddings`, `docs-fetch`, `summarize` |
| Spec §7.1 examples | kebab | `research`, `command-run`, `code-gen` |
| `shared/routing/grpc_adapter.py` | snake | `python`, `javascript`, `bash`, `devops`, `file_edit`, `sql`, `data_analysis` |
| Classifier at runtime | snake | free-form; invents a tag per request |

`_DEFAULT_SYSTEM_PROMPT` asks the model for `"<short-snake_case-tag>"` — an open
vocabulary in the wrong case. Even a conceptually correct `code_gen` cannot
match `code-gen`.

This failed silently for the same reason the withdrawn-model bug did:
`classify()` degrades to a safe default rather than raising, so the only symptom
is uniform routing.

## Decisions

| Question | Decision |
|---|---|
| Case convention | **kebab-case**, everywhere |
| Vocabulary | A **common shared set**; deviation needs a justified use case |
| Where the list lives | **A database table**, so it can be updated without a release |
| Out-of-vocabulary output | Fall through to heuristics; record the rejected tag in the trace |

### Canonical set

**Internal functions** — already seeded by migration 010, unchanged:

`security-audit` · `routing-classifier` · `embeddings` · `docs-fetch` · `summarize`

**Request-facing** — what the classifier may emit:

`code-gen` · `command-run` · `research` · `chat` · `data-analysis` · `ops` · `general`

### Why a table rather than a constant

A shared constant would have to be released to change, and Elder and WaddleBot
would each pin their own copy — reintroducing drift in a different form. A table
is updatable in place, and the products consume the vocabulary from WaddleAI the
same way they consume bundles, so there is one authority rather than N pinned
copies.

It also removes the failure mode that caused this bug in the first place:
**the classifier's system prompt is generated from the table**, so the set the
model is told to choose from and the set assignments are keyed by cannot drift
apart. They are the same rows.

### Why out-of-vocabulary falls through rather than coercing

Coercing an unrecognised tag to `general` would route the request adequately and
destroy the signal. A classifier repeatedly proposing `sql-migration` is telling
the operator the vocabulary needs an entry; that belongs in the trace where it
can be counted, not silently rewritten. Falling through to heuristics is also
the behaviour the cascade already has for a punt, so this adds no new path.

## Architecture

### Storage

`tool_types` — `name` (kebab-case, unique), `kind` (`internal` | `request-facing`),
`description` (used verbatim when generating the classifier prompt), `enabled`,
`created_at`, `updated_at`. Seeded by migration with the canonical set above.

A CHECK or application-level validator rejects a non-kebab-case `name`, so the
standard is enforced at the point of writing rather than by convention.

### Prompt generation

The stage-2 system prompt is built from `tool_types` where `kind =
'request-facing' AND enabled`, replacing the free-form
`"<short-snake_case-tag>"` instruction with an explicit enumeration and each
type's description. Cached, invalidated on write to the table — the same
pattern `security_policies` resolution already uses.

### Reconciling grpc_adapter

`_CODE_TOOLS` / `_OPS_TOOLS` / `_DATA_TOOLS` currently hold snake_case
language and tool names (`file_edit`, `data_analysis`) and map them to coarse
`code`/`ops`/`data`/`general` buckets. These are a different axis — a *target*
category, not a tool type — and the overlap in naming is what makes them look
like a fourth dialect.

They are normalised to kebab-case and their relationship to `tool_types` is made
explicit rather than implied by string equality. This is the part of the work
most likely to surface hidden assumptions, so it is sequenced last.

## Error handling

| Condition | Behaviour |
|---|---|
| Classifier returns a known type | Normal: assignment lookup proceeds |
| Classifier returns an unknown tag | Fall through to heuristics; record the tag in `routing_decision_traces` |
| Classifier returns a non-kebab variant of a known type (`code_gen`) | Normalised to `code-gen` and accepted — a case mismatch is not a vocabulary miss |
| `tool_types` unreadable | Fall back to the last cached vocabulary; never block routing |

## Testing

- **Prompt-generation test** — the generated system prompt contains exactly the
  enabled request-facing types and no others. This is the test that keeps the
  two sides from drifting.
- **Out-of-vocabulary test** — an unknown tag falls through to heuristics AND
  appears in the trace. Asserting only the fallback would pass while the signal
  is silently dropped.
- **Normalisation test** — `code_gen`, `Code-Gen` and `code-gen` all resolve to
  `code-gen`; a genuinely unknown tag still misses.
- **GPU tier, end-to-end** — with a constrained vocabulary and two candidate
  models, a trivial request and a coding request must reach *different* models.
  This is the assertion that currently fails and is the whole point of the work;
  `tests/unit/routing/test_engine_gpu.py` already contains the harness.

## Out of scope

- Which model serves which tool type (that is `model_assignments`, unchanged)
- Model inventory and existence validation (separate spec)
- Classifier bundles (separate spec; bundles and tool types are independent)
