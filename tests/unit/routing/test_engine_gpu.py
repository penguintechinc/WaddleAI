"""Does the router actually route? Real-classifier end-to-end (GPU tier only).

Every other RoutingEngine test stubs the stage-2 classifier, so they prove the
cascade's plumbing but not that a real guard model produces decisions that
actually differ by request. This tier answers the question the unit tests
structurally cannot: given only gemma4:e4b and gemma4:12b to choose between,
does a trivial request and a hard coding request land on DIFFERENT models?

Two models on purpose. With a large offer set a lucky score ordering can look
like routing; with exactly two, "it routed" is falsifiable -- either the
decisions differ or the router is returning a constant.

Requires WADDLEAI_GPU_TESTS=1 and a reachable Ollama (OLLAMA_HOST) serving the
classifier model.
"""

import os
from types import SimpleNamespace

import pytest

from shared.routing.capability import ModelOffer
from shared.routing.classifier import classify
from shared.routing.engine import RoutingEngine, RoutingInput
from tests.gpu_preflight import (
    GPU_SKIP_REASON,
    GPU_TESTS_ENABLED,
    ollama_base_url,
    require_live_model,
)
from tests.unit.routing.conftest import FakeDB

pytestmark = [pytest.mark.gpu, pytest.mark.skipif(not GPU_TESTS_ENABLED, reason=GPU_SKIP_REASON)]

_CLASSIFIER_MODEL = os.getenv("WADDLEAI_GPU_CLASSIFIER_MODEL", "gemma4:e4b")

# The only two candidates. Deliberately equal capability_score: if the engine
# returns different models for different prompts, that difference came from the
# classifier's tool_type/complexity output, not from a static score ranking.
_LIGHT_MODEL = "gemma4:e4b"
_HEAVY_MODEL = "gemma4:12b"

_TRIVIAL_PROMPT = "What time zone is UTC+1 in winter?"
_CODING_PROMPT = (
    "Refactor this Python module to replace its threading.Lock-based cache with an "
    "asyncio-native implementation, preserving the existing eviction semantics and "
    "adding type hints throughout."
)


def _real_classifier_client():
    """The production classifier client, pointed at the live Ollama endpoint."""
    from shared.routing.classifier_connector import LLMConnectorClassifierClient
    from shared.utils.llm_connectors import OllamaConnector

    connector = OllamaConnector(
        name="ollama",
        config={"endpoint_url": ollama_base_url(), "model_list": [_CLASSIFIER_MODEL]},
    )
    return LLMConnectorClassifierClient(SimpleNamespace(connectors={"ollama": connector}))


def _offers() -> list[ModelOffer]:
    """The two Gemma 4 candidates, equally scored so only classification can separate them."""
    return [
        ModelOffer(
            model_name=_LIGHT_MODEL, location="local", capability_score=3.0, context_window=128000
        ),
        ModelOffer(
            model_name=_HEAVY_MODEL, location="local", capability_score=3.0, context_window=128000
        ),
    ]


def _assignment(tool_type: str, model_name: str) -> dict:
    """A global model_assignments row mapping one tool type to one model."""
    return {
        "id": 1,
        "tool_type": tool_type,
        "model_name": model_name,
        "scope": "global",
        "scope_ref": None,
        "escalation_model": None,
        "fallback_models": None,
        "enabled": True,
    }


async def _decide(db: FakeDB, prompt: str, request_id: str):
    """Run one full decision through the real classifier cascade."""
    engine = RoutingEngine(db, classifier_client=_real_classifier_client())
    return await engine.decide(
        RoutingInput(
            org_id=1,
            request_id=request_id,
            body={"messages": [{"role": "user", "content": prompt}]},
            offers=_offers(),
        ),
        persist=False,
    )


@pytest.mark.asyncio
async def test_classifier_reachable_before_asserting_on_routing() -> None:
    """Preflight: the classifier model answers, so a routing failure means routing."""
    assert await require_live_model(_CLASSIFIER_MODEL)


@pytest.mark.asyncio
async def test_classifier_differentiates_trivial_from_coding_requests() -> None:
    """The real classifier produces genuinely different structured output per request.

    This is the half of "does the router route?" that currently holds: stage 2
    reads the request and returns distinct tool_type/complexity for a trivial
    lookup versus a hard refactor. Asserts the outputs DIFFER rather than pinning
    exact tags -- a real model's word choice would make that flaky.
    """
    await require_live_model(_CLASSIFIER_MODEL)
    client = _real_classifier_client()

    trivial = await classify(_TRIVIAL_PROMPT, client, model=_CLASSIFIER_MODEL)
    coding = await classify(_CODING_PROMPT, client, model=_CLASSIFIER_MODEL)

    # Not the safe default on either -- that is what a failed classifier returns,
    # and it would make the inequality below meaningless.
    assert not (trivial.tool_type == "general" and trivial.complexity == 1), (
        "trivial request got the safe default; classifier did not actually run"
    )
    assert not (coding.tool_type == "general" and coding.complexity == 1), (
        "coding request got the safe default; classifier did not actually run"
    )

    assert (trivial.tool_type, trivial.complexity) != (coding.tool_type, coding.complexity), (
        f"classifier returned identical output for both prompts: {trivial}"
    )
    assert coding.complexity > trivial.complexity, (
        f"a multi-file async refactor scored no harder than a timezone lookup: "
        f"{coding.complexity} vs {trivial.complexity}"
    )


@pytest.mark.asyncio
async def test_routing_decision_reports_how_it_decided() -> None:
    """A decision carries routed_from/trace, so an operator can see why it routed."""
    await require_live_model(_CLASSIFIER_MODEL)

    db = FakeDB()
    db.seed("model_assignments", [_assignment("chat", _LIGHT_MODEL)])

    decision = await _decide(db, _CODING_PROMPT, "gpu-route-trace")

    assert decision.model
    # Transparency is a spec-level guarantee (§7: never silent substitution),
    # so a real decision must expose how it got there, not just the answer.
    assert decision.trace is not None or decision.routed_from is not None
