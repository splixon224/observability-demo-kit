"""OpenTelemetry SDK setup untuk observability-demo-kit.

Ekspos `tracer` dan `logger` singleton agar app.py tinggal gunakan.
Tidak membaca kredensial apa pun — hanya env var OTel standar.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import Counter, Histogram, generate_latest

# Nama demo service — bisa ditimpa lewat env SERVICE_NAME (stabil).
SERVICE_NAME = os.environ.get("SERVICE_NAME", "observability-demo")

OTEL_ENDPOINT = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "http://localhost:4317",
)

_resource = Resource.create({"service.name": SERVICE_NAME})


def _configure() -> dict[str, Any]:
    """Setup SDK sekali (idempotent via singleton otel globals)."""

    # Traces
    _tp = TracerProvider(resource=_resource)
    _tp.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT, insecure=True)))
    trace.set_tracer_provider(_tp)

    # Metrics — OTLP gRPC (ke collector). Prometheus reader di-handle lewat prometheus_client langsung.
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    _grpc = OTLPMetricExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    _mp = MeterProvider(resource=_resource, metric_readers=[PeriodicExportingMetricReader(_grpc)])
    metrics.set_meter_provider(_mp)

    # Logs — LoggingHandler menyambungkan stdlib logging → OTLP
    _lp = LoggerProvider(resource=_resource)
    _lp.add_log_record_processor(BatchLogRecordProcessor(
        OTLPLogExporter(endpoint=OTEL_ENDPOINT, insecure=True)
    ))
    logging.getLogger().addHandler(LoggingHandler(level=logging.INFO, logger_provider=_lp))

    # Instrumentations
    LoggingInstrumentor().instrument()

    return {
        "tracer": trace.get_tracer(__name__),
        "meter": metrics.get_meter(__name__),
        "generate_latest": generate_latest,
    }


_cfg = _configure()
tracer = _cfg["tracer"]
logger = logging.getLogger(__name__)  # logger Python standar sudah di-patch otomatis

# Counter & histogram demo — pakai prometheus_client langsung agar /metrics stabil.
http_requests_total = Counter(
    "demo_http_requests_total",
    "Jumlah request HTTP masuk ke demo app",
    labelnames=["method", "path", "status_code"],
)
http_request_latency = Histogram(
    "demo_request_latency_seconds",
    "Latensi request HTTP (jam oleh FlaskInstrumentor juga)",
    labelnames=["method", "path"],
)


def instrument_app(app) -> None:
    """Patch Flask app dengan OTel instrumentation."""
    FlaskInstrumentor().instrument(app=app)


def get_prometheus_output() -> bytes:
    """Render semua collector + custom counter/histogram."""
    return generate_latest()
