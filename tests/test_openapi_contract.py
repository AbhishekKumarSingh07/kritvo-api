from pathlib import Path

from kritvo.tools.openapi import DEFAULT_OUTPUT, render

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_committed_contract_is_current() -> None:
    committed = (REPO_ROOT / DEFAULT_OUTPUT).read_text(encoding="utf-8")
    assert committed == render(), "Run `uv run kritvo-openapi` and commit openapi/openapi.json"


def test_health_endpoint_is_in_contract() -> None:
    assert '"/healthz"' in render()
