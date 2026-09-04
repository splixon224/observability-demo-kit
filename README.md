# observability-demo-kit

![python](https://img.shields.io/badge/python-3.11-blue) ![docker](https://img.shields.io/badge/docker-compose%203%20services-2496ED) ![tests](https://img.shields.io/badge/pytest-10%2F10-brightgreen)

Demo kit observability lengkap dalam satu `docker compose up`: aplikasi Flask kecil yang menghasilkan **logs, metrics, dan distributed traces**, dikumpulkan OTel Collector, dan disimpan/di-query lewat **OpenObserve** — semua komponen 100% open-source, biaya nol. Cocok sebagai template belajar observability atau starter untuk stack monitoring kamu sendiri.

## Arsitektur

```
┌─────────────────┐   OTLP gRPC/HTTP   ┌──────────────────────┐   OTLP/HTTP    ┌─────────────────────┐
│  Demo App       │ ─────────────────▶ │  OTel Collector      │ ─────────────▶ │  OpenObserve        │
│  Flask :5081    │                    │  :4317 / :4318       │                │  :5080 (UI + API)   │
└─────────────────┘                    └──────────────────────┘                └─────────────────────┘
     /healthz /metrics /generate          pipelines: logs+metrics+traces        Log Explorer · Metrics · Traces
```

## Quickstart

```bash
git clone https://github.com/splixon224/observability-demo-kit.git
cd observability-demo-kit
cp .env.example .env          # isi ZO_ROOT_USER_EMAIL & ZO_ROOT_USER_PASSWORD kamu
docker compose up -d          # 3 service: app, collector, observe

curl http://localhost:5081/healthz          # {"status": "ok"}
curl -X POST http://localhost:5081/generate # hasilkan telemetri sintetis
```

Lalu buka **http://localhost:5080/web/** dan login dengan `ZO_ROOT_USER_EMAIL` — kamu akan melihat logs, metrics, dan traces masuk secara real-time.

## Endpoint Demo App

| Endpoint | Fungsi |
|---|---|
| `GET /healthz` | Health check → `{"status": "ok"}` |
| `GET /metrics` | Format Prometheus — `demo_http_requests_total` + `demo_request_latency_seconds` |
| `POST /generate` | Generate 5 log lines (level campuran) + 1 trace span, return JSON hitungan |

## Environment Variables

| Variabel | Dipakai oleh | Deskripsi |
|---|---|---|
| `ZO_ROOT_USER_EMAIL` | observe | Email root user OpenObserve (login UI + API) |
| `ZO_ROOT_USER_PASSWORD` | observe | Password root user OpenObserve |
| `OBSERVE_AUTH` | collector | Header Basic auth untuk ingest ke OpenObserve |
| `OBSERVE_ENDPOINT` | collector | URL ingest OTLP OpenObserve |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | app | Endpoint collector untuk export telemetri |

> Semua nilai rahasia hanya lewat `.env` (sudah di-gitignore). Tidak ada kredensial di dalam kode.

## Testing

```bash
python3 -m pytest tests/ -q
# 10 passed — mencakup healthz, metrics counter, generate JSON,
# import tanpa error, dan deteksi anti-hardcode-secret (AST-based)
```

## Struktur Repo

```
observability-demo-kit/
├── app/
│   ├── app.py              # Flask demo app (3 endpoint)
│   └── instrumentation.py  # OTel SDK: tracer, logger, instrumentor
├── static/
│   └── index.html          # Lite UI status (Logs/Metrics/Traces)
├── tests/                  # 10 tests (pytest, tanpa network)
├── collector-config.yaml   # OTel Collector: receivers otlp → exporter otlphttp
├── Dockerfile              # python:3.11-slim multi-purpose
├── docker-compose.yml      # 3 services + volume + healthchecks
├── .env.example            # template env vars
└── requirements.txt
```

## Built by AI Employees Org

Proyek ini dibangun end-to-end oleh organisasi AI employees (orchestrated via [Hermes Agent](https://github.com/splixon224)):

- **Rani** (Product Analyst) — spec GATE 1: 5 fitur + 5 acceptance criteria terukur
- **Bagas** (Architect) — scaffold repo & struktur
- **Fajar** (Backend Dev) — Flask app + OTel instrumentation
- **Dika** (Frontend Dev) — Dockerfile, collector config, static UI
- **Nadia** (QA) — test suite 10 tests (termasuk anti-hardcode-secret)
- **Yoga** (DevOps) — docker-compose + deploy + healthcheck

Pipeline: spec → build (paralel) → QA → deploy. Setiap agent menulis progres + event log-nya sendiri.
