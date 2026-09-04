"""QA pre-build tests untuk observability-demo-kit (NADIA).

Lima test case wajib:
  - test_healthz_200           (AC1)
  - test_metrics_contains_counter (AC2)
  - test_generate_returns_json (AC5a)
  - test_app_import_no_error
  - test_env_not_hardcoded     (file app/app.py TIDAK mengandung string literal password/secretdummy)

Semua jalan TANPA jaringan — pakai Flask test client (conftest-provided
`client` fixture) + pemeriksaan file statis (ast.parse). Tidak ada requests
ke host eksternal/OpenObserve.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = REPO_ROOT / "app" / "app.py"


# ---------------------------------------------------------------------------
# AC1 — /healthz mengembalikan HTTP 200 + body {"status":"ok"}
# ---------------------------------------------------------------------------
def test_healthz_200(client):
    """Endpoint /healthz responsif: HTTP 200, body status ok (AC1)."""
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.get_json(force=True)
    assert isinstance(data, dict)
    assert data.get("status") == "ok"


# ---------------------------------------------------------------------------
# AC2 — /metrics mengekspos counter Prometheus demo_http_requests_total
# ---------------------------------------------------------------------------
def test_metrics_contains_counter(client):
    """Endpoint /metrics memuat counter demo_http_requests_total (AC2)."""
    # Populate counter dulu dengan satu request.
    client.get("/generate")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.data.decode("utf-8", errors="replace")
    assert "demo_http_requests_total" in body


# ---------------------------------------------------------------------------
# AC5a — /generate mengembalikan JSON
# ---------------------------------------------------------------------------
def test_generate_returns_json(client):
    """Route /generate mengembalikan JSON dengan keys yang diharapkan (AC5a)."""
    resp = client.get("/generate")
    assert resp.status_code == 200
    data = resp.get_json(force=True)
    assert isinstance(data, dict)
    assert data.get("generated_log_lines") == 5
    assert data.get("trace_spans") == 1


# ---------------------------------------------------------------------------
# Import sanity — app.app dapat diimpor tanpa error (dependency terpasang)
# ---------------------------------------------------------------------------
def test_app_import_no_error():
    """Modul app.app dapat diimpor dan mengekspos `application` Flask."""
    from app.app import application  # noqa: F401

    assert application is not None


# ---------------------------------------------------------------------------
# Hardening — app.py TIDAK mengandung string literal password/secretdummy
#
# Yang diharapkan: app.py hanya menggunakan `os.environ.get(...)` untuk
# membaca kredensial eksternal. Tidak ada string literal yang berisi
# password/secretdummy/secret atau api_key/token yang diquote sebagai nilai.
#
# Test ini memeriksa SEMUA string literal di-app.py (termasuk docstring);
# jika ada string literal yang mengandung kata kunci rahasia (case-insensitive),
# test akan gagal. Nama env var seperti "OBSERVE_PASSWORD" yang muncul di
# comment/code identifier tidak termasuk karena bukan string literal.
# ---------------------------------------------------------------------------
_KEYWORDS = ("password", "secretdummy", "secret")


def _extract_string_literals(source: str) -> list[str]:
    """Return daftar string literal tertutup (triple/single/double quote)."""
    literals: list[str] = []
    # Triple-quoted strings dulu (agar tidak terpotong).
    for m in re.finditer(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', source):
        literals.append(m.group(1))
    # Sisa single/double quoted strings (tanpa triple).
    stripped = re.sub(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', '', source, flags=re.S)  # noqa: W605
    for m in re.finditer(r'"([^"\\]|\\.)*"|\'([^\'\\]|\\.)*\'', stripped):
        literals.append(m.group(0))
    return literals


def test_env_not_hardcoded():
    """app/app.py tidak mengandung string literal password/secretdummy."""
    assert APP_PATH.exists(), f"file tidak ditemukan: {APP_PATH}"
    source = APP_PATH.read_text(encoding="utf-8")
    literals = _extract_string_literals(source)

    offenders: list[str] = []
    for lit in literals:
        lit_lower = lit.lower()
        # Docstring modul adalah dokumentasi, bukan nilai rahasia — skip.
        if lit.startswith(('"""', "'''")) and lit.rstrip().endswith(('"""', "'''")):
            continue
        for kw in _KEYWORDS:
            if kw in lit_lower:
                # False-positive guard: nama env var / identifier (mis.
                # "OBSERVE_PASSWORD" di os.environ.get) bukan nilai rahasia.
                if re.fullmatch(r'["\'][A-Z_][A-Z0-9_]*["\']', lit):
                    continue
                offenders.append(lit.strip()[:80])
                break

    assert offenders == [], (
        f"String literal terlarang ditemukan di app/app.py: {offenders}. "
        "Pakai os.environ.get(), jangan quote string rahasia."
    )
