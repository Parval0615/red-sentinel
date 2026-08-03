from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_API_PATH = REPO_ROOT / "docs" / "api" / "public-api.json"


def test_stable_public_api_allowlist_is_documented() -> None:
    """Keep the stable API explicit and reject undocumented public entry points."""
    policy = json.loads(PUBLIC_API_PATH.read_text(encoding="utf-8"))

    assert policy["schema_version"] == "public-api-documentation-v1"
    assert policy["modules"]

    failures: list[str] = []
    for module_name, symbols in policy["modules"].items():
        module = importlib.import_module(module_name)
        for symbol_name in symbols:
            if not hasattr(module, symbol_name):
                failures.append(f"{module_name}.{symbol_name}: missing")
                continue
            symbol = getattr(module, symbol_name)
            if not (inspect.isclass(symbol) or inspect.isfunction(symbol)):
                failures.append(f"{module_name}.{symbol_name}: not a class or function")
            elif not inspect.getdoc(symbol):
                failures.append(f"{module_name}.{symbol_name}: missing docstring")

    assert failures == []


def test_public_api_policy_explains_compatibility_exclusions() -> None:
    policy = json.loads(PUBLIC_API_PATH.read_text(encoding="utf-8"))
    exclusions = " ".join(policy["policy"]["exclusions"]).lower()

    assert "legacy compatibility" in exclusions
    assert "type aliases" in exclusions
