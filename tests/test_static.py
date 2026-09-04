import os
import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_static_index_contains_required_strings():
    index_path = os.path.join(REPO_ROOT, "static", "index.html")
    assert os.path.exists(index_path), "static/index.html harus ada"
    with open(index_path, encoding="utf-8") as f:
        content = f.read()
    assert "OpenTelemetry" in content, "index.html harus mengandung 'OpenTelemetry'"
    assert "Logs" in content, "index.html harus mengandung 'Logs'"


def test_collector_config_valid_and_has_required_keys():
    config_path = os.path.join(REPO_ROOT, "collector-config.yaml")
    assert os.path.exists(config_path), "collector-config.yaml harus ada"
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    assert isinstance(cfg, dict)
    for key in ("receivers", "exporters", "service"):
        assert key in cfg, f"collector-config.yaml harus punya key '{key}'"
