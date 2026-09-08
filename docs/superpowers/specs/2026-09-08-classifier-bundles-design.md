# Classifier Bundles — Design

**Date:** 2026-09-08
**Status:** Design approved, not yet planned or implemented
**Owner decisions captured in:** this document's Decisions table

## Problem

WaddleAI's security auditor is a small guard model (`shieldgemma:2b`) asked to
recognise attacks it was never shown. Live testing on 2026-09-08 found it
"doesn't catch a ton on its own" — it has no knowledge of a given deployment's
tool surface, nor of specific attack techniques.

Separately, products that integrate WaddleAI (Elder, WaddleBot) have no way to
say *which* kinds of classification they want. Today the choice is the whole
policy or nothing: `security_policies.intent_categories` is a flat list resolved
per-org, with no name, no version, and no per-request selection.

Both problems have the same shape — classification is configured as loose
category strings rather than as coherent, named, knowledge-carrying units.

## Solution

A **classifier bundle** is a named, versioned unit that carries everything
needed to classify one concern area: its categories, the guard prompt fragment
that defines them, the retrieval corpus that teaches the guard what they look
like, and what to do when each matches.

Consumers name the bundles they want per request. Enabling a bundle enables its
knowledge.

## Decisions

| Question | Decision |
|---|---|
| Where bundles live | WaddleAI hosts them; consumers select per-call |
| Selection semantics | **Additive only** — a caller may add, never remove |
| Bundle contents | Categories + guard prompt + RAG corpus + per-category action |
| Transport | `X-CLASSIFIER-BUNDLES` request header |
| Security guard | **Always on**; disableable only by the WaddleAI global admin |
| Tenant always-on set | A **tenant admin** configures which bundles are always-on for their tenant; callers cannot remove them |
| Authoring | PenguinTech-shipped only for now; schema leaves room for org-authored later |
| Licensing | **Free tier** — bundles are not license-gated |

### Why additive-only

A per-request parameter that can weaken protection is a bypass vector: a bug or
compromise in an integration silently drops classification the org intended, and
nothing objects. Union-at-every-level makes weakening structurally impossible
rather than merely discouraged, and matches the monotonic-composition property
the spec's §8.5 filter-integrity rules already depend on.

### Why Free tier

Safety classification is not an upsell. Bundles ship unGated so every
deployment classifies by default; the PostHog feature flag still applies (every
feature is flagged, defaulted OFF until validated) but there is no
`license_client.has_feature()` check on bundle selection or execution.

> **Open item for confirmation:** `critical-rules.md`'s tier table lists
> "WaddleAI" itself among Enterprise-gated features. "Bundles are Free" is
> unambiguous *within* WaddleAI, but the tier table may need wording so the two
> statements don't read as contradictory to someone implementing a gate.

## Architecture

### Bundle definition (source of truth)

Bundles are reviewed source in the repo, seeded into the database by migration.
Orgs enable and disable; they do not author.

```
bundles/
  security-attack/
    bundle.yaml          categories, actions, guard prompt fragment, version
    corpus/
      attack-techniques.md
      tool-abuse-patterns.md
  hate-speech/
    bundle.yaml
    corpus/*.md
  pii-basic/
    bundle.yaml
    corpus/*.md
```

```yaml
# bundles/security-attack/bundle.yaml
name: security-attack
version: 1.0.0
mandatory: true            # global-mandatory; only a global admin may disable
categories:
  malware-generation:    {action: block}
  exploit-development:   {action: block}
  credential-harvesting: {action: block}
guard_prompt: |
  ...definition of each category, in the guard's instruction slot...
recommended_guard: shieldgemma:2b
```

`recommended_guard` is advisory. The model that actually runs is resolved from
`model_assignments` (`security-audit` tool type), so a deployment can run Granite
Guardian instead without forking the bundle.

### Storage

- `classifier_bundles` — `name`, `version`, `scope` (`global` only today, column
  present so org-authored bundles are a later migration rather than a redesign),
  `categories` JSON, `guard_prompt`, `mandatory`, `enabled`, timestamps.
- `classifier_bundle_corpus` — `bundle_id`, `doc_path`, `content`, `embedding`.
  Retrieval reuses the existing knowledge layer (`shared/knowledge/`) rather than
  introducing a second vector store.
- `classifier_bundles_tenant` — `org_id`, `bundle_id`, `always_on`, `updated_by`,
  `updated_at`. The tenant admin's always-on set, and an audit trail of who
  changed it. A row here can only add to the platform floor; the API rejects an
  attempt to mark a platform-mandatory bundle as off.

### Composition

Three levels, unioned. No level can narrow the one above it.

```
platform floor     [security-attack]   WaddleAI global admin only
      ∪
tenant always-on   [pii-basic,         tenant admin configures
                    hate-speech]        (classifier_bundles_tenant)
      ∪
caller header      [brand-safety]      X-CLASSIFIER-BUNDLES
      =
effective          [security-attack, pii-basic, hate-speech, brand-safety]
```

Resolution reuses `security_policies`' existing global → org → user → key
resolver. No second resolution path is introduced.

**Each level may only widen the one above it.** A tenant admin decides their
tenant's always-on set and can add anything to it, but cannot subtract from the
platform floor — removing the security guard remains a WaddleAI global admin
action alone. A caller cannot subtract from either. The property holds
transitively: no actor can produce an effective set smaller than the union of
the levels above them.

This is deliberately a **tenant-admin surface, not just a config value**. The
people who know which bundles their organisation must always run are that
organisation's admins; the platform's job is to make their choice
unremovable-by-callers, not to make it for them. The platform floor exists only
for what PenguinTech will not let any tenant switch off.

**Global admin kill switch.** Disabling the mandatory security guard is a
deliberate, audited action: an audit row recording who, when and why, plus a
stderr banner at startup for as long as it stays off. A disabled guard must not
be able to sit unnoticed.

### Request contract

```http
POST /v1/chat/completions
X-CLASSIFIER-BUNDLES: hate-speech,security-attack
```

A header rather than a body field so the OpenAI-compatible request schema stays
untouched and every SDK can set it without special handling — the same reasoning
behind `X-WaddleAI-Tool-Type`.

Naming note: the header is deliberately `X-CLASSIFIER-BUNDLES`, not
`...-MODELS`. Its values are bundle names; `X-Preferred-Model` already exists and
selects an actual model. Two headers with "model" in the name doing unrelated
things would be misused.

**An unknown bundle name is a 400, not a silent skip.** If a caller sends
`hate_speech` for `hate-speech`, ignoring it leaves the caller believing it is
protected when it is not. Fail closed and loud.

**The response reports what actually ran**, in `usage.waddleai.classifiers`:
the effective bundle list with versions, and which level contributed each. Same
rule as `routed_from` — never a silent substitution, and a caller can confirm
its addition took effect.

### Corpus into the guard

Retrieved corpus documents are placed in the guard's **instruction** portion,
never in the data slot holding user content. Mixing them would make the corpus
its own injection vector, which §8.5's content-is-data rule exists to prevent.

This is the part that answers the ShieldGemma gap directly: the guard stops
classifying cold, because enabling a bundle supplies the documentation of what
that bundle's attacks look like.

## Error handling

| Condition | Behaviour |
|---|---|
| Unknown bundle name in header | 400, naming the unknown bundle |
| Bundle enabled but corpus retrieval fails | Classify without retrieval, log a warning; degraded, not skipped |
| Guard model unreachable | Existing `fail_mode` from the resolved policy governs; unchanged |
| Mandatory guard disabled by global admin | Audit row + startup banner, every request |
| Tenant admin tries to disable a platform-floor bundle | 403; the floor is not theirs to lower |

## Testing

- **Composition property tests** — for any (platform, tenant, caller) combination,
  the effective set is a superset of platform ∪ tenant. This is the
  security-critical invariant, so it is tested as a property rather than by
  example, including the case where a tenant admin attempts to unset a
  platform-floor bundle.
- **Unknown-bundle rejection** — a typo'd name 400s and does not classify.
- **Response reporting** — `usage.waddleai.classifiers` names every effective
  bundle and its version.
- **Per-bundle recorded-verdict fixtures** — stubbed guard in the default tier.
- **GPU tier** — real `shieldgemma:2b` against real bundles, measuring whether
  corpus-backed classification actually outperforms cold classification. That
  premise is the whole reason for the design; if it does not hold, the corpus
  layer needs rethinking before it ships.

## Out of scope

- Org-authored bundle *definitions* (schema is ready; surface stays closed).
  Note this is distinct from the tenant always-on *selection* above, which IS
  in scope: tenants choose which shipped bundles are mandatory for them, they
  just cannot author new ones yet.
- Per-bundle model selection (stays in `model_assignments`)
- Any relaxation of additive-only composition
