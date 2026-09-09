"""OpenTelemetry metrics bootstrap and instrument registry.

Mirrors ``tracing.py``: configured from environment, and a no-op when
``OTEL_EXPORTER_OTLP_ENDPOINT`` is unset so the app starts without an exporter.

This module deliberately does NOT replace ``shared/utils/metrics.py``
(prometheus_client). The two coexist during the transition; new instruments go
here, and the Prometheus surface stays until its consumers move.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

from opentelemetry import metrics
from opentelemetry.sdk.resources import Resource

logger = logging.getLogger(__name__)

_meter: metrics.Meter | None = None
_initialized = False


@dataclass(slots=True)
class MetricsConfig:
    """OpenTelemetry metrics configuration from environment."""

    otlp_endpoint: str | None = None
    service_name: str = "waddleai"
    service_version: str = "unknown"
    deployment_environment: str = "development"

    @classmethod
    def from_env(cls) -> "MetricsConfig":
        """Load configuration from the same variables tracing uses."""
        service_version = "unknown"
        if os.path.exists(".version"):
            try:
                with open(".version") as f:
                    service_version = f.read().strip()
            except OSError as e:
                logger.warning(f"Failed to read .version file: {e}")
        return cls(
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            service_name=os.getenv("OTEL_SERVICE_NAME", "waddleai"),
            service_version=service_version,
            deployment_environment=os.getenv("OTEL_DEPLOYMENT_ENVIRONMENT", "development"),
        )


def init_metrics(config: MetricsConfig | None = None) -> metrics.Meter:
    """Initialize the OTel MeterProvider, or leave the API's no-op in place.

    With no OTLP endpoint configured this installs nothing and returns the
    default no-op meter, so instrument calls are cheap and never raise. Failing
    to reach a collector must never take the request path down.
    """
    global _meter, _initialized
    if _initialized and _meter is not None:
        return _meter

    cfg = config or MetricsConfig.from_env()
    if not cfg.otlp_endpoint:
        logger.info("OTel metrics disabled (no OTEL_EXPORTER_OTLP_ENDPOINT); using no-op meter")
        _meter = metrics.get_meter(cfg.service_name)
        _initialized = True
        return _meter

    try:
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

        resource = Resource.create(
            {
                "service.name": cfg.service_name,
                "service.version": cfg.service_version,
                "deployment.environment": cfg.deployment_environment,
            }
        )
        reader = PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=cfg.otlp_endpoint))
        metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[reader]))
        logger.info(f"OTel metrics exporting to {cfg.otlp_endpoint}")
    except Exception as e:  # pragma: no cover - exporter/collector setup failure
        # Never fail startup over telemetry: fall through to the no-op meter.
        logger.warning(f"OTel metrics init failed, continuing without export: {e}")

    _meter = metrics.get_meter(cfg.service_name)
    _initialized = True
    return _meter


def get_meter() -> metrics.Meter:
    """The process meter, initializing from environment on first use."""
    if _meter is None:
        return init_metrics()
    return _meter


_pii_detected: Any = None


def pii_detected_counter() -> Any:
    """Counter for PII detections, labelled by type/phase/action.

    Labels are bounded by construction: ``pii_type`` is a rule name from a
    finite rule set, ``phase`` is input|output, ``action`` is the filter's
    decision. The matched TEXT is never a label -- it is unbounded and it is the
    very PII being reported.
    """
    global _pii_detected
    if _pii_detected is None:
        _pii_detected = get_meter().create_counter(
            "waddleai.pii.detected",
            unit="1",
            description="PII matches found by the content filter, by type",
        )
    return _pii_detected


def reset_for_testing() -> None:
    """Drop cached meter and instruments so a test can install its own provider."""
    global _meter, _initialized, _pii_detected
    _meter = None
    _initialized = False
    _pii_detected = None
