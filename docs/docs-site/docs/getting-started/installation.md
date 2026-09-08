# Installation Guide

WaddleAI has three deployable services — **proxy** (OpenAI-compatible data plane, port 8080 + gRPC 50051), **management** (Flask/Quart control plane, port 8001), and **webui** (port 8080 in-container, static React shell) — plus PostgreSQL and Valkey. Kubernetes via Helm is the only supported deployment path; Docker Compose is deprecated across the project and this repo does not ship a `docker-compose.yml`.

## Prerequisites

- Python 3.13 (services and tooling; hash-pinned lockfiles require it)
- PostgreSQL 14+ with the `pgvector` extension (memory/RAG vector storage) — SQLite works for quick local experiments but is not the supported production database
- Valkey (Redis-protocol cache) — used for routing/session cache and rate limiting
- Node.js 24.x — only if you're building/running the webui outside its container
- `kubectl` + Helm v4, and a local cluster (MicroK8s on Linux, Docker Desktop Kubernetes on macOS/Windows) if you want the full stack running in Kubernetes
- `git`, `uv` (for `make venv`)

## GPU requirements (local model serving)

Only needed if you serve models locally via Ollama. A deployment that routes
exclusively to commercial providers needs no GPU at all.

### The e4b-only baseline

The minimum viable local set is three models — the routing classifier, the
always-on security auditor, and the embedding model:

| Model | Role | VRAM |
|---|---|---|
| `gemma4:e4b` | routing classifier, summarize, docs-fetch | 3.26 GB |
| `shieldgemma:2b` | security auditor (always on) | 2.14 GB |
| `nomic-embed-text` | embeddings | 0.32 GB |
| **Total** | | **5.72 GB** |

Measured with all three resident simultaneously on a live host, Q4_K_M
quantization. These are **base weights at idle** — the KV cache grows on top of
them as context length and concurrency increase, and that growth is what
actually determines whether a card holds up.

### Minimum and recommended

| | VRAM | Example cards | Reality |
|---|---|---|---|
| **Minimum** | 8 GB | RTX 4060, RTX 5060 | Works. ~2.3 GB left for KV cache after the base set — enough for short contexts and low concurrency, tight for anything else |
| **Recommended** | 12 GB+ | RTX 3060 12GB, RTX 4070 | Comfortable headroom for long contexts, concurrent requests, and `gemma4:12b` for coding roles |

8 GB is a real floor, not a comfortable one. Pushing an 8 GB card to its limit
with an LLM plus two embedding-class models leaves very little room for the KV
cache to expand during long sessions or high-throughput retrieval. Budget for a
display buffer too if the card is also driving a monitor.

### Adding gemma4:12b for coding

`gemma4:12b` is the default for coding roles (orchestration, exploration) and
costs **8.42 GB** once it has context — more than the entire e4b-only set.

**The binding constraint is a config default, not VRAM.** Ollama's
`OLLAMA_MAX_LOADED_MODELS` defaults to **3**. WaddleAI's full local set is
**four** models — `gemma4:e4b`, `gemma4:12b`, `shieldgemma:2b`,
`nomic-embed-text` — so one is always evicted no matter how much VRAM the card
has. Measured on a 16 GB host:

| Models requested | Resident | Total VRAM |
|---|---|---|
| `e4b`, `shieldgemma`, `nomic` | 3 | 5.72 GB |
| `12b`, `shieldgemma`, `nomic` | 3 | 10.89 GB |
| `e4b`, `12b`, `shieldgemma` | 3 | **13.49 GB** |
| all four | **3** — one evicted | 5.72 GB |

The third row is the proof: 13.49 GB stays resident without complaint, so
memory is not what is stopping the fourth model. Buying a larger card does not
fix this.

```bash
# on the Ollama host
OLLAMA_MAX_LOADED_MODELS=4   # or higher, if you serve more models
```

**Why it matters.** `gemma4:e4b` is the routing classifier, so it runs on every
request that reaches stage 2; `gemma4:12b` serves coding requests. If the cap
evicts one of them, a coding workload alternates between the two and each
alternation is an evict-and-reload. Nothing errors — throughput simply
collapses, and the cause is invisible unless you check `/api/ps`:

```bash
curl -s http://<host>:11434/api/ps | python3 -m json.tool | grep -E '"name"|size_vram'
```

Fewer models listed than you serve means the cap is evicting, and raising
`OLLAMA_MAX_LOADED_MODELS` — not more VRAM — is the fix.

**VRAM still matters, separately.** Once the cap is raised, all four must
actually fit: 5.72 GB (baseline) + 8.42 GB (`12b` with context) ≈ **14.2 GB of
weights**, plus KV headroom.

| Serving | VRAM | Example cards | Notes |
|---|---|---|---|
| e4b only | 8 GB min / 12 GB rec | RTX 4060 / RTX 3060 12GB | See table above |
| **e4b + 12b** | **16 GB** | RTX 4080, RTX 3090, mobile RTX 3080 16GB | Verified: 13.49 GB co-resident. Requires Q4 and managed context |
| e4b + 12b, comfortable | **24 GB** | RTX 3090 / 4090 | Room for Q8 or unquantized 12B and 8K+ contexts |

Quantization is what makes this fit. At Ollama's default **Q4_K_M** the 12B
model is ~7.5–8.5 GB; at Q8 it is ~13–14 GB and at BF16 ~24–27 GB. A stack that
fits comfortably at Q4 will OOM at Q8 on the same card — or worse, Ollama
silently offloads layers to system RAM and generation speed collapses without an
error.

An 8 GB card cannot host `12b` alongside the baseline at all. It will OOM
immediately or fall back to CPU/RAM offloading.

#### Squeezing 12b onto a tight card: the QAT tag

`gemma4:12b-it-qat` is a quantization-aware-trained variant (the tag exists in
Ollama's published list). QAT quantizes during training rather than after, so it
tends to preserve more reasoning quality than post-training quantization at a
comparable footprint, and it is reported to run a few hundred MB smaller than
the standard `gemma4:12b` Q4_K_M.

Treat the saving as worth testing, not as a given. **Measured here,
`gemma4:12b` is 8.09 GB idle and 8.42 GB with context** — higher than the
~7.6 GB commonly cited for Q4_K_M, so published deltas may not transfer to this
deployment.

The only question worth measuring is whether the QAT variant leaves
`gemma4:e4b` resident alongside it. If it does, the thrashing above disappears;
if it does not, a few hundred MB changed nothing that matters. Check with:

```bash
curl -s http://<host>:11434/api/ps | python3 -m json.tool | grep -E '"name"|size_vram'
```

If `gemma4:e4b` is missing from that output after a coding request, the stack is
still thrashing regardless of which 12B tag is loaded.

### A note on model sizes

Do not size from the download. `gemma4:e4b` is **9.61 GB on disk but 3.26 GB
resident**, because its MatFormer packaging ships more weights than the
effective-4B submodel actually loads. By contrast `gemma4:12b` is 7.56 GB on
disk and 8.09 GB resident. The disk figure alone would tell you e4b is the more
expensive model, which is backwards.

## Option A: Kubernetes with Helm (recommended)

The Helm chart at `k8s/helm/waddleai` is the only supported deployment path for every environment (alpha, beta, production). Full walkthrough, values-file reference, and ingress/TLS setup: [Kubernetes Deployment](../deployment/kubernetes.md).

Quick path for a local alpha cluster (MicroK8s or Docker Desktop Kubernetes, `local-alpha` kubectl context):

```bash
git clone https://github.com/penguintechinc/waddleai.git
cd waddleai
./scripts/deploy-alpha.sh   # builds proxy/management/webui images, loads them into the
                             # cluster's local image store, then:
                             # helm upgrade --install waddleai k8s/helm/waddleai \
                             #   --kube-context local-alpha --namespace waddleai \
                             #   --create-namespace --values k8s/helm/waddleai/values-alpha.yaml
```

`./scripts/deploy-beta.sh` deploys the same chart with `values-beta.yaml` to the shared beta cluster (CI-built on merge to `main` — `ghcr.io/penguintechinc/waddleai/{proxy,management,webui}:beta-<epoch64>` images — never build beta/prod images locally). There is no `values-production.yaml` in this repo yet; production deployments start from `values.yaml` with an operator-supplied overlay — see [Kubernetes Deployment](../deployment/kubernetes.md) for the current guidance and the full five-tier release pipeline.

## Option B: Local development

For running the Python services directly against your own Postgres/Valkey — full detail, troubleshooting, and the local-Kubernetes alternative live in [docs/DEVELOPMENT.md](../DEVELOPMENT.md). Summary:

```bash
git clone https://github.com/penguintechinc/waddleai.git
cd waddleai

# make venv is the only supported local setup: uv-managed .venv (Python 3.13)
# installed from the hash-pinned requirements*.txt lockfiles. A bare host
# python3 is not supported here even if 3.13 is on PATH — dependency
# resolution and CI both go through this venv.
make venv
```

Start Postgres (with pgvector) and Valkey as standalone containers — there is no Compose file:

```bash
docker run -d --name waddleai-postgres \
  -e POSTGRES_DB=waddleai -e POSTGRES_USER=waddleai -e POSTGRES_PASSWORD=waddleai-dev \
  -p 5432:5432 pgvector/pgvector:pg16

docker run -d --name waddleai-valkey -p 6379:6379 valkey/valkey:8-bookworm
```

Run each service from the repo root with `.venv` active (`--reload` restarts on save; `make dev` currently shells out to `docker-compose up`, which does not work in this repo since no `docker-compose.yml` exists — use the commands below instead):

```bash
# Management API (port 8001) — start first, the proxy talks to it at startup
export PYTHONPATH="$(pwd):$(pwd)/services/management"
export DATABASE_URL=postgresql://waddleai:waddleai-dev@localhost:5432/waddleai
export JWT_SECRET=$(openssl rand -hex 32)
cd services/management && .venv/bin/hypercorn asgi:app --bind 0.0.0.0:8001 --reload
```

```bash
# Proxy (port 8080, gRPC 50051)
export PYTHONPATH="$(pwd):$(pwd)/proxy"
export DATABASE_URL=postgresql://waddleai:waddleai-dev@localhost:5432/waddleai
cd proxy && ../.venv/bin/hypercorn apps.proxy_server.main:app --bind 0.0.0.0:8080 --reload
```

```bash
# Web UI (port 3000, proxies /api/* to localhost:8001) — optional for API-only use
cd services/webui && npm ci && npm run dev
```

## Configuration

Every service reads environment variables directly — there is no `.env.example` in this repo. Only vars actually read by the code are listed below (checked against `shared/`, `proxy/`, `services/`); anything else you may see in older docs or examples elsewhere is not consumed.

| Variable | Required | Default | Read by |
|---|---|---|---|
| `DATABASE_URL` | Recommended (postgres) | `sqlite:///waddleai.db` fallback | `shared/database/models.py`, `services/management/app/config.py` |
| `DB_TYPE`, `DB_USER`, `DB_PASS`, `DB_NAME` | No — alternative to `DATABASE_URL` | `sqlite` / unset | `services/management/app/config.py` |
| `JWT_SECRET` | **Yes**, production | `""` (insecure) | `services/management/app/config.py`, proxy auth |
| `FLASK_SECRET_KEY` | No | falls back to `JWT_SECRET` | `services/management/app/config.py` |
| `ADMIN_INITIAL_PASSWORD` | No | random, un-loggable, if unset | `services/management/app/extensions.py` |
| `WEBHOOK_SECRET` | Yes, if using webhooks | `""` | `services/management/app/config.py` |
| `CREDENTIAL_ENCRYPTION_KEY` | Recommended | unset → stored LLM-provider credentials are unencrypted | `shared/security/credential_encryption.py` |
| `HTTP_PORT` | No | `8080` | `proxy/apps/proxy_server/main.py` |
| `GRPC_PORT` | No | `50051` | `proxy/apps/proxy_server/main.py` |
| `MANAGEMENT_SERVER_URL` | No | `http://localhost:8001` | `proxy/apps/proxy_server/main.py` |
| `REDIS_URL` | No | `redis://localhost:6379/0` | `proxy/apps/proxy_server/main.py` (Valkey, despite the name) |
| `CACHE_HOST`, `CACHE_PORT`, `CACHE_USER`, `CACHE_PASS` | No | unset | `services/management/app/config.py` (also honors `REDIS_URL`) |
| `LICENSE_KEY`, `PRODUCT_NAME` | No — required only to unlock licensed tiers | unset | `shared/licensing/python_client.py` |
| `LICENSE_SERVER_URL` | No | `https://license.penguintech.io` | `shared/licensing/python_client.py`, `proxy/apps/proxy_server/main.py` |
| `NER_SPACY_MODEL` | No | `en_core_web_lg` (~425MB installed) | `shared/security/ner_filter.py`, `shared/security/content_filter.py` |
| `WADDLEAI_NER_ALLOW_DOWNLOAD` | No | unset → NER PII tier disabled if the pinned model isn't already installed | `shared/security/ner_filter.py` |
| `SECURITY_POLICY` | No | `balanced` (`strict`/`balanced`/`permissive`) | `proxy/apps/proxy_server/main.py` |
| `CORS_ORIGINS` | No | `*` | `services/management/app/config.py` |
| `LOG_LEVEL` | No | `INFO` | multiple |

Set `NER_SPACY_MODEL=en_core_web_md` for a much smaller image (~32MB) at some cost in PII-entity detection accuracy — the model itself is still a hash-pinned wheel pull at build time, this only changes which one.

## First run

WaddleAI never prints an admin API key to logs. On first startup with an empty database, the management service creates a `default` organization and an `admin` user (`services/management/app/extensions.py`):

- If `ADMIN_INITIAL_PASSWORD` was set, that's the admin password. Otherwise a random password is generated and **not logged anywhere** — set `ADMIN_INITIAL_PASSWORD` explicitly before first boot if you need to know it.
- An admin virtual key is created and stored only as a bcrypt hash; the plaintext value is never printed or recoverable. Don't rely on it — create your own key instead:

1. Log in to the webui (or `POST /api/v1/auth/login` with the admin username/password) to get a JWT.
2. Create a virtual key for yourself: `POST /api/v1/keys` with that JWT as a bearer token. The response's `api_key` field is shown exactly once — save it immediately.

```bash
curl -s -X POST http://localhost:8001/api/v1/keys \
  -H "Authorization: Bearer $ADMIN_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-first-key", "tpm_limit": 10000, "rpm_limit": 60}'
```

## Verify

```bash
# Proxy
curl http://localhost:8080/healthz
curl http://localhost:8080/readyz     # 200 once the database dependency is healthy

# Management
curl http://localhost:8001/healthz
curl http://localhost:8001/readyz

export WADDLEAI_API_KEY="<your-waddleai-key>"

curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer $WADDLEAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

## Next steps

- [Local Development Guide](../DEVELOPMENT.md) — full local workflow, Alembic migrations, hot-reload
- [Kubernetes Deployment](../deployment/kubernetes.md) — Helm chart, values files, ingress/TLS
- [Connect Claude Code](../integrations/claude-code.md)
- [OpenCode integration](../integrations/opencode.md)
