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
from types import SimpleNamespace

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


class _RecordingClassifierClient:
    """The PRODUCTION classifier client, wrapped to keep each raw reply.

    Deliberately wraps ``LLMConnectorClassifierClient`` rather than calling the
    Ollama connector directly: that class supplies the baked-in JSON-shape
    system prompt (``_DEFAULT_SYSTEM_PROMPT``) used whenever an org has not
    configured ``routing_policies.classifier_prompt``. A test that built its own
    connector would send the bare user prompt, get prose back, and blame the
    model for what is really a missing instruction.

    The recorded raw text is what lets a test tell a genuine classification from
    ``classify()``'s silent safe-default fallback.
    """

    def __init__(self) -> None:
        from shared.routing.classifier_connector import LLMConnectorClassifierClient
        from shared.utils.llm_connectors import OllamaConnector

        # `endpoint_url`, not `base_url`: LLMConnector.__init__ reads
        # config["endpoint_url"], and a wrong key leaves it None so every request
        # goes to the literal URL "None/api/chat". An earlier version of this test
        # used "base_url" and still passed, because classify() swallows the
        # failure and returns its safe default.
        connector = OllamaConnector(
            name="ollama",
            config={"endpoint_url": ollama_base_url(), "model_list": [_CLASSIFIER_MODEL]},
        )
        self._manager = SimpleNamespace(connectors={"ollama": connector})
        self._inner = LLMConnectorClassifierClient(self._manager)
        self.raw_replies: list[str] = []

    async def complete(self, prompt: str, model: str, system_prompt: str | None = None) -> str:
        """Delegate to the production client, recording the raw reply."""
        text = await self._inner.complete(prompt, model, system_prompt=system_prompt)
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
    client = _RecordingClassifierClient()

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
