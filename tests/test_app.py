"""Tests untuk demo app observability-demo-kit.

Semua test berjalan TANPA jaringan — hanya Flask test client.
conftest.py sudah memperbaiki sys.path, jadi `import app.app` langsung jalan.
"""

from __future__ import annotations


def test_healthz_200(client):
    """AC 1: GET /healthz → 200, body {"status":"ok"}."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_metrics_contains_counter(client):
    """AC 2: GET /metrics → 200, body memuat demo_http_requests_total + histogram."""
    client.get("/healthz")  # populate counter/histogram labels
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8", errors="replace")
    assert "demo_http_requests_total" in body
    assert "demo_request_latency_seconds" in body


def test_generate_returns_json(client):
    """GET /generate → 200 JSON: 5 log lines + 1 trace span."""
    resp = client.get("/generate")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data["generated_log_lines"] == 5
    assert data["trace_spans"] == 1
