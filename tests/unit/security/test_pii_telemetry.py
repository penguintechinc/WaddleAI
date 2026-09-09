"""PII detection must emit real OTel metrics, not merely declare instruments.

Captures actual data points through an InMemoryMetricReader rather than
asserting a counter object exists -- a declared-but-never-incremented
instrument is exactly the silent failure this telemetry is meant to prevent.
"""

from collections.abc import Iterator

import pytest
from opentelemetry import metrics as otel_metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

from shared.observability import metrics as obs_metrics
from shared.security.content_filter import ContentFilter

_PII_TEXT = "Email alice.smith@example.com, card 4111 1111 1111 1111, SSN 123-45-6789."


@pytest.fixture
def captured() -> Iterator[InMemoryMetricReader]:
    """Install a real MeterProvider whose data points a test can read back."""
    reader = InMemoryMetricReader()
    otel_metrics._internal._METER_PROVIDER = None  # allow re-set within a session
    otel_metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
    obs_metrics.reset_for_testing()
    yield reader
    obs_metrics.reset_for_testing()


def _points(reader: InMemoryMetricReader, name: str) -> list:
    """Every data point recorded for one instrument name."""
    data = reader.get_metrics_data()
    out = []
    for rm in getattr(data, "resource_metrics", []) or []:
        for sm in rm.scope_metrics:
            for m in sm.metrics:
                if m.name == name:
                    out.extend(m.data.data_points)
    return out


@pytest.mark.asyncio
async def test_pii_detection_emits_a_metric_point_per_type(captured) -> None:
    """Three kinds of PII produce three labelled data points, with real counts."""
    await ContentFilter(db=None).filter_input(_PII_TEXT, user_id=1, org_id=1)

    points = _points(captured, "waddleai.pii.detected")
    assert points, "no waddleai.pii.detected data points were recorded at all"

    by_type = {p.attributes["pii_type"]: p.value for p in points}
    for expected in ("email", "credit_card", "ssn"):
        assert expected in by_type, f"{expected} missing from {sorted(by_type)}"
        assert by_type[expected] >= 1


@pytest.mark.asyncio
async def test_pii_metric_records_phase_and_action(captured) -> None:
    """Attributes carry the operational context, not just a bare count."""
    await ContentFilter(db=None).filter_input(_PII_TEXT, user_id=1, org_id=1)

    points = _points(captured, "waddleai.pii.detected")
    assert all(p.attributes["phase"] == "input" for p in points)
    assert all(p.attributes["action"] in {"redact", "block", "log"} for p in points)


@pytest.mark.asyncio
async def test_pii_metric_never_carries_the_matched_text(captured) -> None:
    """The matched value must not reach telemetry.

    Unbounded as a label, and it is the very data being protected -- a metrics
    pipeline is precisely where PII must not be re-introduced.
    """
    await ContentFilter(db=None).filter_input(_PII_TEXT, user_id=1, org_id=1)

    for p in _points(captured, "waddleai.pii.detected"):
        flattened = " ".join(f"{k}={v}" for k, v in p.attributes.items())
        for secret in ("alice.smith@example.com", "4111 1111 1111 1111", "123-45-6789"):
            assert secret not in flattened, f"{secret!r} leaked into metric attributes"


@pytest.mark.asyncio
async def test_clean_text_emits_nothing(captured) -> None:
    """No PII, no data points -- otherwise the counter cannot signal anything."""
    await ContentFilter(db=None).filter_input("What is the CAP theorem?", user_id=1, org_id=1)

    assert not _points(captured, "waddleai.pii.detected")
