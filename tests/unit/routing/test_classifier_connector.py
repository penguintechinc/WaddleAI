"""Regression tests: the classifier must disable model-side thinking.

Gemma 4 reasons by default. Its thinking tokens are billed against the request's
token budget and returned in NEITHER `response` nor `thinking`, so a caller with
a modest budget receives an empty string and no error. `classify()` reads that as
malformed output and degrades to tool_type="general", complexity=1 -- which makes
every request route identically while nothing anywhere reports a problem.

Measured against a live host before the fix: gemma4:12b returned 0 characters
through this path, gemma4:e4b happened to fit inside the 200-token budget and
worked. So the bug was invisible on the default model and fatal on a model the
WebUI dropdown openly offers.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from shared.routing.classifier_connector import LLMConnectorClassifierClient


def _client_with_spy() -> tuple[LLMConnectorClassifierClient, AsyncMock]:
    """A classifier client whose single connector records its chat_completion kwargs."""
    connector = SimpleNamespace(
        model_list=["gemma4:e4b"],
        chat_completion=AsyncMock(return_value=('{"tool_type": "chat", "complexity": 1}', {})),
    )
    client = LLMConnectorClassifierClient(SimpleNamespace(connectors={"ollama": connector}))
    return client, connector.chat_completion


@pytest.mark.asyncio
async def test_classifier_sends_think_false() -> None:
    """The classifier disables thinking, so its token budget buys output not reasoning."""
    client, spy = _client_with_spy()

    await client.complete("refactor this module", "gemma4:e4b")

    assert spy.await_args is not None, "connector was never called"
    assert spy.await_args.kwargs["think"] is False, (
        "classifier must send think=False; without it a thinking model consumes the "
        "token budget and returns an empty string, which classify() silently "
        "degrades to the safe default"
    )


@pytest.mark.asyncio
async def test_classifier_still_caps_its_token_budget() -> None:
    """think=False does not replace the budget -- both are needed."""
    client, spy = _client_with_spy()

    await client.complete("refactor this module", "gemma4:e4b")

    assert spy.await_args is not None, "connector was never called"
    assert spy.await_args.kwargs["max_tokens"] > 0
    assert spy.await_args.kwargs["temperature"] == 0.0


@pytest.mark.asyncio
async def test_ollama_connector_forwards_think_to_the_api() -> None:
    """OllamaConnector puts `think` in the payload only when a caller sets it.

    Only-when-set matters: sending it unconditionally would push a field at every
    model, including ones with no thinking mode, for no benefit.
    """
    from unittest.mock import MagicMock, patch

    from shared.utils.llm_connectors import OllamaConnector

    captured: dict = {}

    class _Resp:
        status = 200

        async def json(self):
            return {"message": {"content": "ok"}, "eval_count": 1, "prompt_eval_count": 1}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

    def _post(url, json=None, timeout=None):
        captured.update(json or {})
        return _Resp()

    conn = OllamaConnector(name="ollama", config={"endpoint_url": "http://x:11434"})
    with patch.object(conn, "_session", MagicMock(post=_post, closed=False)):
        await conn.chat_completion([{"role": "user", "content": "hi"}], "gemma4:e4b", think=False)
        assert captured["think"] is False

        captured.clear()
        await conn.chat_completion([{"role": "user", "content": "hi"}], "gemma4:e4b")
        assert "think" not in captured
