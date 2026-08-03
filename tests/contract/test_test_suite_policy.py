from __future__ import annotations

import sys
from pathlib import Path

from conftest import _layer_marker

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - Python 3.10 is the oldest supported interpreter.
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[2]


def _pytest_config() -> dict:
    with (REPO_ROOT / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)["tool"]["pytest"]["ini_options"]


def test_default_collection_covers_every_formal_test_surface() -> None:
    config = _pytest_config()

    assert set(config["testpaths"]) == {
        "tests",
        "frontend/tests",
        "experiments/tests",
    }


def test_default_suite_selects_only_offline_fast_tests() -> None:
    config = _pytest_config()

    assert config["addopts"] == "-m fast"


def test_execution_and_layer_markers_are_registered() -> None:
    config = _pytest_config()
    marker_names = {entry.split(":", 1)[0] for entry in config["markers"]}

    assert {
        "fast",
        "docker",
        "external_model",
        "research_full",
        "unit",
        "contract",
        "integration",
        "research",
        "regression",
    } <= marker_names


def test_layer_mapping_covers_current_test_layouts() -> None:
    assert _layer_marker(Path("tests/unit/test_example.py")) == "unit"
    assert _layer_marker(Path("tests/contract/test_example.py")) == "contract"
    assert _layer_marker(Path("tests/architecture/test_example.py")) == "contract"
    assert _layer_marker(Path("tests/regression/evaluation/contracts/test_example.py")) == "contract"
    assert _layer_marker(Path("tests/regression/evaluation/integration/test_example.py")) == "integration"
    assert _layer_marker(Path("tests/research/test_example.py")) == "research"
    assert _layer_marker(Path("experiments/tests/test_example.py")) == "research"
    assert _layer_marker(Path("frontend/tests/test_example.py")) == "regression"
