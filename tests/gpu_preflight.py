"""Shared preflight for the `gpu`-marked test tier (real Ollama-served models).

Exists because every model-backed code path in WaddleAI degrades gracefully by
design -- ``classify()`` falls back to ``tool_type="general"`` on any error and
``ContentFilter._invoke_llm_auditor`` fail-opens with ``"auditor unavailable"``.
A GPU test that only asserts "a result came back" therefore passes against a
dead endpoint, proving nothing. This module makes the tier prove the model is
actually answering before any test asserts on its output, and FAILS rather than
skips when it is not: the tier only runs when explicitly asked for, so a missing
model is a failure, not a reason to report a silent pass.
"""

import os

import aiohttp
import pytest

GPU_TESTS_ENABLED = os.getenv("WADDLEAI_GPU_TESTS", "").lower() in ("1", "true", "yes")

GPU_SKIP_REASON = (
    "nightly/GPU CI tier only -- set WADDLEAI_GPU_TESTS=1 with a reachable Ollama endpoint"
)


def ollama_base_url() -> str:
    """Ollama endpoint for the GPU tier, defaulting to a local daemon."""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434")


async def require_live_model(model: str) -> str:
    """Assert `model` is served and answering, returning its raw reply text.

    Performs a real ``/api/chat`` round trip rather than only listing tags: a
    pulled-but-unloadable model (out of VRAM, corrupt blob) still appears in
    ``/api/tags``. Calls ``pytest.fail`` on any failure so the tier cannot
    report a pass without having exercised the model.
    """
    url = ollama_base_url()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url}/api/chat",
                json={
                    "model": model,
                    "stream": False,
                    "messages": [{"role": "user", "content": "Reply with the single word: ready"}],
                },
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status != 200:
                    body = (await resp.text())[:200]
                    pytest.fail(
                        f"GPU preflight: {url} returned HTTP {resp.status} for model "
                        f"{model!r}: {body}"
                    )
                payload = await resp.json()
    except aiohttp.ClientError as exc:
        pytest.fail(f"GPU preflight: cannot reach Ollama at {url}: {exc!r}")
    except TimeoutError:
        pytest.fail(f"GPU preflight: {url} timed out loading model {model!r}")

    text = str(payload.get("message", {}).get("content", "")).strip()
    if not text:
        pytest.fail(f"GPU preflight: model {model!r} at {url} returned an empty completion")
    return text
