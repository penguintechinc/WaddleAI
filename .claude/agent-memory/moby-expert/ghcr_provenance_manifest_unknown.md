---
name: ghcr-provenance-manifest-unknown
description: build-push-action v7 default provenance/sbom attestations break GHCR multi-arch imagetools merge and downstream pulls with "manifest unknown" / blob "not found" errors
type: project
---

`.github/workflows/docker-build.yml`'s `build-platform` job (per-arch build via `docker/build-push-action@...v7`, then `merge-manifests` job does `docker buildx imagetools create` to stitch `-amd64`/`-arm64` tags into one multi-arch tag) hit persistent GHCR failures even after the images built and pushed successfully:

- `merge-manifests (proxy)`: `imagetools create` fails with `httpReadSeeker: failed open: ... not found` on a **different blob digest every retry** (5x backoff already in place from an earlier fix).
- `integration-test`: `docker compose pull` of the plain per-arch tag (`proxy:ci-amd64-<sha>`) gets a bare `manifest unknown`, sometimes tens of minutes after the push completed — too late to be simple read-after-write propagation lag.

**Root cause**: `build-push-action` v7 defaults `provenance: true`, which makes buildx attach a second `unknown/unknown` attestation manifest to the pushed image index. `imagetools create` then tries to copy that attestation manifest's blobs too; a plain pull of the tag can also resolve to the broken index. Well-documented: docker/build-push-action#851, #764, #900; docker/buildx community discussion #45969.

**Fix**: add `provenance: false` and `sbom: false` to every `docker/build-push-action` step in this repo's workflows — not more retries, not a `needs:`/tag-name change (those were both already correct here). A different-digest-each-retry pattern is the tell that distinguishes this bug from genuine eventual-consistency lag (which converges on the *same* digest).

**Why it surfaced on the proxy image specifically**: proxy is ML-heavy (torch + spaCy `en_core_web_lg`, multi-GB) — the extra attestation write is heaviest there — but the bug applies to any image built through a `build-push-action` step without `provenance: false`, including `build-ollama-image` in the same file.

**How to apply**: before adding retry/backoff as the fix for any future GHCR "manifest unknown" / blob "not found" report in this repo, check whether the failure pattern shows a *different* missing digest on each attempt (this bug) vs the *same* digest resolving after a short wait (real propagation lag, where retry is the correct fix — see the existing `merge-manifests` retry, added in `7f91fd2f`, which is legitimate defense-in-depth once provenance is disabled).

See also: PR #162 (fix/ghcr-proxy-manifest-unknown), commit `7f91fd2f` (prior retry-only fix that was necessary but not sufficient).
