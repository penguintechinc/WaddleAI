"""Real-model classifier fixture test (spec §14.4): nightly/GPU CI tier only.

Deselected in the default unit run -- exercises the real gemma4:e4b guard model
via the fleet's Ollama connector instead of StubClassifierClient.

``classify()`` degrades to ``tool_type="general", complexity=1`` on ANY failure,
including an unreachable endpoint, so asserting only "a Classification came
back" passes against a dead host. These tests therefore record the model's raw
completion and assert it parsed, rather than trusting the degraded default. See
``tests/gpu_preflight``.

Requires WADDLEAI_GPU_TESTS=1 and a reachable Ollama endpoint (OLLAMA_HOST).
"""

import json
import os

import pytest

from shared.routing.classifier import classify
from tests.gpu_preflight import (
    GPU_SKIP_REASON,
    GPU_TESTS_ENABLED,
    ollama_base_url,
    require_live_model,
)

pytestmark = [pytest.mark.gpu, pytest.mark.skipif(not GPU_TESTS_ENABLED, reason=GPU_SKIP_REASON)]

# The MINIMUM supported Gemma 4 tag, not the recommended one. gemma4:12b is what
# the house guidance recommends for general generation, but the routing
# classifier's floor is e4b and this tier's job is to prove the floor holds --
# testing only the recommendation would let the floor rot unnoticed.
_CLASSIFIER_MODEL = os.getenv("WADDLEAI_GPU_CLASSIFIER_MODEL", "gemma4:e4b")


class _RecordingOllamaClassifierClient:
    """ClassifierClient over the real Ollama connector that keeps each raw reply.

    The raw text is what lets a test tell a genuine classification from
    ``classify()``'s silent safe-default fallback.
    """

    def __init__(self) -> None:
        from shared.utils.llm_connectors import OllamaConnector

        self._connector = OllamaConnector(name="ollama", config={"base_url": ollama_base_url()})
        self.raw_replies: list[str] = []

    async def complete(self, prompt: str, model: str, system_prompt: str | None = None) -> str:
        """Call the model, record the raw reply, and return it unchanged."""
        messages = ([{"role": "system", "content": system_prompt}] if system_prompt else []) + [
            {"role": "user", "content": prompt}
        ]
        text, _usage = await self._connector.chat_completion(messages=messages, model=model)
        self.raw_replies.append(text)
        return text


@pytest.mark.asyncio
async def test_classifier_model_is_actually_serving() -> None:
    """Preflight: the classifier model answers a real chat call before anything asserts on it."""
    reply = await require_live_model(_CLASSIFIER_MODEL)
    assert reply


@pytest.mark.asyncio
async def test_real_gemma4_e4b_classifies_a_coding_prompt() -> None:
    """The real minimum-bar model returns a parseable structured classification."""
    await require_live_model(_CLASSIFIER_MODEL)
    client = _RecordingOllamaClassifierClient()

    result = await classify(
        "Write a Python function that reverses a linked list.",
        client,
        model=_CLASSIFIER_MODEL,
    )

    # Proves the model was actually consulted -- classify() swallows every
    # exception, so without this the safe default would look like a pass.
    assert client.raw_replies, "classifier client was never invoked"
    raw = client.raw_replies[0]
    assert raw.strip(), "model returned an empty completion"

    # And proves the reply was usable: the degraded path is reached precisely
    # when the reply does not parse into the expected object.
    parsed = json.loads(raw[raw.index("{") : raw.rindex("}") + 1])
    assert "tool_type" in parsed, f"no tool_type in model output: {raw[:200]!r}"

    assert result.tool_type
    assert 1 <= result.complexity <= 5
