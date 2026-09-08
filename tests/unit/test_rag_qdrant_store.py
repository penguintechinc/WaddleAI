"""Unit tests for ``QdrantRAGStore.search`` against the pinned qdrant-client==1.19.0 API.

``QdrantClient.search()`` was removed from the pinned client in favor of
``query_points()``, whose response wraps hits in ``.points`` rather than
returning a bare iterable. A previous pass left the old ``.search()`` call in
place behind a ``cast(Any, client)``, so it raised ``AttributeError`` at
runtime on every call and the surrounding ``except Exception`` silently
swallowed it into an empty result list -- a permanent, silent "no results".
These tests exercise the fixed ``query_points`` call path and guard against
the old call being reintroduced.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchValue

from shared.utils import rag_integration
from shared.utils.rag_integration import QdrantRAGStore


class _FakeEmbeddingArray:
    """Stand-in for the numpy array `SentenceTransformer.encode()` returns.

    Only implements `.tolist()`, the one method `_generate_embedding` calls.
    """

    def __init__(self, values: list[float]) -> None:
        """Store the fixed embedding values to hand back from `tolist()`."""
        self._values = values

    def tolist(self) -> list[float]:
        """Return the embedding as a plain list, matching numpy's API."""
        return self._values


class _FakeEncoder:
    """Stand-in for `SentenceTransformer` that never loads real model weights."""

    def encode(self, text: str, convert_to_tensor: bool = False) -> _FakeEmbeddingArray:
        """Return a fixed, deterministic fake embedding regardless of input."""
        return _FakeEmbeddingArray([0.1, 0.2, 0.3])


def _scored_point(payload: dict | None, score: float) -> SimpleNamespace:
    """Build a `ScoredPoint`-shaped double: payload + score is all `search()` reads."""
    return SimpleNamespace(payload=payload, score=score)


def _query_response(points: list[SimpleNamespace]) -> SimpleNamespace:
    """Build a `QueryResponse`-shaped double whose hits live under `.points`."""
    return SimpleNamespace(points=points)


@pytest.fixture
def qdrant_store(monkeypatch: pytest.MonkeyPatch) -> QdrantRAGStore:
    """Build a QdrantRAGStore with a fake encoder and a spec'd mock client.

    Patches `_sentence_transformer` before construction so `__init__` never
    imports/loads a real SentenceTransformer model (slow, network-dependent).
    The client is `spec=QdrantClient`, so accessing a nonexistent attribute
    like `.search` raises `AttributeError` immediately -- exactly like the
    real pinned client -- instead of silently returning a MagicMock.
    """
    monkeypatch.setattr(rag_integration, "_sentence_transformer", lambda name: _FakeEncoder())
    store = QdrantRAGStore()
    store.client = MagicMock(spec=QdrantClient)
    return store


def _mock_client(store: QdrantRAGStore) -> MagicMock:
    """The store's mocked client, typed so Mock assertion attributes resolve.

    ``QdrantRAGStore.client`` is declared ``QdrantClient | None``, so mypy sees
    the real method signatures and rejects ``.return_value`` /
    ``.assert_called_once()``. The cast is test-only and does not weaken the
    ``spec=QdrantClient`` guard, which is what makes a reintroduced
    ``.search()`` call raise at runtime.
    """
    return cast(MagicMock, store.client)


@pytest.mark.asyncio
async def test_search_returns_documents_from_query_points(qdrant_store: QdrantRAGStore) -> None:
    """search() maps QueryResponse.points hits into SearchResult with distance = 1 - score."""
    response = _query_response(
        [
            _scored_point(
                {"doc_id": "doc-1", "content": "hello world", "metadata": {"lang": "en"}},
                0.9,
            ),
            _scored_point(
                {"doc_id": "doc-2", "content": "bonjour monde", "metadata": {"lang": "fr"}},
                0.75,
            ),
        ]
    )
    _mock_client(qdrant_store).query_points.return_value = response

    results = await qdrant_store.search("hello", collection="kb", limit=5, min_score=0.5)

    assert len(results) == 2
    assert results[0].document.id == "doc-1"
    assert results[0].document.content == "hello world"
    assert results[0].document.metadata == {"lang": "en"}
    assert results[0].document.collection == "kb"
    assert results[0].score == 0.9
    assert results[0].distance == pytest.approx(1.0 - 0.9)

    assert results[1].document.id == "doc-2"
    assert results[1].score == 0.75
    assert results[1].distance == pytest.approx(1.0 - 0.75)


@pytest.mark.asyncio
async def test_search_calls_query_points_with_expected_kwargs(
    qdrant_store: QdrantRAGStore,
) -> None:
    """search() passes query=<embedding> (not query_vector=) and keeps limit/score_threshold."""
    _mock_client(qdrant_store).query_points.return_value = _query_response([])

    await qdrant_store.search("hello", collection="kb", limit=3, min_score=0.42)

    _mock_client(qdrant_store).query_points.assert_called_once()
    _, kwargs = _mock_client(qdrant_store).query_points.call_args
    assert kwargs["collection_name"] == "kb"
    assert kwargs["query"] == [0.1, 0.2, 0.3]
    assert kwargs["limit"] == 3
    assert kwargs["score_threshold"] == 0.42
    assert "query_vector" not in kwargs


@pytest.mark.asyncio
async def test_search_handles_missing_payload(qdrant_store: QdrantRAGStore) -> None:
    """A hit with payload=None (allowed by ScoredPoint) does not raise; fields fall back."""
    _mock_client(qdrant_store).query_points.return_value = _query_response(
        [_scored_point(None, 0.6)]
    )

    results = await qdrant_store.search("hello")

    assert len(results) == 1
    assert results[0].document.id == ""
    assert results[0].document.content == ""
    assert results[0].document.metadata == {}


@pytest.mark.asyncio
async def test_search_builds_filter_from_filters_arg(qdrant_store: QdrantRAGStore) -> None:
    """filters={"category": ...} becomes a Filter(must=[FieldCondition(...)]) query_filter."""
    _mock_client(qdrant_store).query_points.return_value = _query_response([])

    await qdrant_store.search("hello", filters={"category": "docs"})

    _, kwargs = _mock_client(qdrant_store).query_points.call_args
    query_filter = kwargs["query_filter"]
    assert isinstance(query_filter, Filter)
    assert query_filter.must == [
        FieldCondition(key="metadata.category", match=MatchValue(value="docs"))
    ]


@pytest.mark.asyncio
async def test_search_without_filters_passes_none_query_filter(
    qdrant_store: QdrantRAGStore,
) -> None:
    """No filters arg means query_filter=None is passed through to query_points."""
    _mock_client(qdrant_store).query_points.return_value = _query_response([])

    await qdrant_store.search("hello")

    _, kwargs = _mock_client(qdrant_store).query_points.call_args
    assert kwargs["query_filter"] is None


@pytest.mark.asyncio
async def test_search_uses_query_points_never_search(qdrant_store: QdrantRAGStore) -> None:
    """Regression: the removed `.search()` call must never come back.

    `_mock_client(qdrant_store)` is `spec=QdrantClient`, and `QdrantClient` in the
    pinned 1.19.0 has no `search` attribute at all -- so if `search()` were
    reintroduced, accessing `client.search` would raise `AttributeError`
    (caught by the method's own `except Exception`, producing an empty
    result list) rather than ever reaching `query_points`. This test fails
    loudly on that regression by asserting `query_points` was in fact
    called, and that `.search` does not exist on the spec'd mock.
    """
    _mock_client(qdrant_store).query_points.return_value = _query_response(
        [_scored_point({"doc_id": "doc-1", "content": "x", "metadata": {}}, 0.8)]
    )

    results = await qdrant_store.search("hello")

    _mock_client(qdrant_store).query_points.assert_called_once()
    assert len(results) == 1

    with pytest.raises(AttributeError):
        _ = _mock_client(qdrant_store).search


@pytest.mark.asyncio
async def test_search_returns_empty_list_on_no_embedding(
    qdrant_store: QdrantRAGStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If embedding generation fails (returns None), search short-circuits to []."""
    monkeypatch.setattr(qdrant_store, "_generate_embedding", lambda text: None)

    results = await qdrant_store.search("hello")

    assert results == []
    _mock_client(qdrant_store).query_points.assert_not_called()


@pytest.mark.asyncio
async def test_search_swallows_query_points_exception(qdrant_store: QdrantRAGStore) -> None:
    """An exception from query_points itself is still caught, returning [] (unchanged contract)."""
    _mock_client(qdrant_store).query_points.side_effect = RuntimeError("connection refused")

    results = await qdrant_store.search("hello")

    assert results == []
