# observability-demo-kit

> **Catatan:** Header README final akan difinalisasi oleh Fajar.

---

## Stack
- Flask + OpenTelemetry (OTLP) + OpenObserve
- Prometheus client untuk metrics
- pytest untuk testing

## Struktur
```
observability-demo-kit/
├── app/
│   ├── __init__.py
│   ├── app.py              # Fajar
│   └── instrumentation.py  # Fajar
├── tests/
│   ├── __init__.py
│   └── test_observability.py  # Nadia
├── collector-config.yaml   # Dika
├── Dockerfile              # Dika
├── docker-compose.yml      # Yoga
├── requirements.txt
└── README.md
```

## Quickstart (setelah implementasi)
```bash
pip install -r requirements.txt
pytest tests/ -v
```
