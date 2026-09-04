"""Pytest fixture & conftest untuk observability-demo-kit.

Fix sys.path agar `import app.app` bekerja tanpa PYTHONPATH.
Semua test dijalankan dengan Flask test client (tidak ada jaringan).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Repo root = parent dari tests/
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ.setdefault("SERVICE_NAME", "observability-demo-test")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

from app.app import application  # noqa: E402

@pytest.fixture
def client():
    application.config.update({
        "TESTING": True,
    })
    with application.test_client() as c:  # noqa: SIM117
        yield c
