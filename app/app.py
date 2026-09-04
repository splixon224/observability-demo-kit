"""Demo Flask app untuk observability-demo-kit.

Routes:
  /   → redirect ke /healthz
  /healthz → JSON status ok
  /metrics → Prometheus exposition
  /generate → buat synthetic logs + 1 trace span dummy, return JSON jumlah

Secret/kredensial tidak di-hardcode. Ambil dari env var (OBSERVE_USER / OBSERVE_PASSWORD)
jika diperlukan oleh komponen lain; app ini sendiri tidak menggunakannya.
"""

from __future__ import annotations

import logging
import os
import time

from flask import Flask, jsonify, redirect, request, Response

from app.instrumentation import (
    http_request_latency,
    http_requests_total,
    instrument_app,
    tracer,
)

app = Flask(__name__)

# Kredensial external (jika ada) — hanya baca, tidak hardcode.
OBSERVE_USER = os.environ.get("OBSERVE_USER", "")
OBSERVE_PASSWORD = os.environ.get("OBSERVE_PASSWORD", "")


@app.before_request
def _before():
    request.environ["REQUEST_TIME"] = time.time()


@app.after_request
def _after(response):
    code = response.status_code
    method = request.method
    path = request.path
    http_requests_total.labels(method=method, path=path, status_code=code).inc()
    start = request.environ.get("REQUEST_TIME", time.time())
    http_request_latency.labels(method=method, path=path).observe(time.time() - start)
    return response


instrument_app(app)


@app.route("/")
def index():
    return redirect("/healthz", code=302)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.route("/metrics")
def metrics():
    from app.instrumentation import get_prometheus_output
    resp = Response(get_prometheus_output(), mimetype="text/plain; charset=utf-8")
    return resp


@app.route("/generate")
def generate():
    """Membuat 5 log lines dengan level campuran + 1 trace span dummy."""
    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    logger = logging.getLogger("app.app")
    count = 0

    for lvl in levels:
        getattr(logger, lvl.lower())(f"Synthetic log line #{count}: [{lvl}] demo message")
        count += 1

    with tracer.start_as_current_span("generate_work") as span:
        span.set_attribute("app.phase", "generate")
        span.set_attribute("app.logs_generated", count)
        for i in range(count):
            span.add_event(f"trace-log-{i}", {"seq": i, "level": levels[i]})

    return jsonify({"generated_log_lines": count, "trace_spans": 1, "total_events": count})


# Ekspose app untuk werkzeug/devserver
application = app
