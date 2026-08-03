from pathlib import Path

from redsentinel.runtime.engine.sandbox.replay import CassetteStore


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())


def test_cassette_turn_index_matching() -> None:
    cassette = CassetteStore(
        ROOT / "tests" / "fixtures" / "cassettes" / "direct_api" / "p1-sandbox-5step-direct-api" / "seed_42.yaml"
    )
    assert cassette.exists
    turn0 = cassette.response_json_for_turn(0)
    assert turn0["choices"][0]["message"]["tool_calls"][0]["function"]["name"] == "get_weather"
    turn2 = cassette.response_json_for_turn(2)
    assert "Beijing" in turn2["choices"][0]["message"]["content"]
