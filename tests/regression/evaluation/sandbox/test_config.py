from pathlib import Path


from redsentinel.runtime.engine.sandbox.config import ScenarioConfig


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "pyproject.toml").is_file())


def test_load_direct_api_scenario() -> None:
    path = ROOT / "configs" / "scenarios" / "p1-sandbox-5step-direct-api.yaml"
    config = ScenarioConfig.from_yaml(path)
    assert config.agent.framework == "direct_api"
    assert config.runner.max_steps == 5


def test_load_langgraph_scenario() -> None:
    path = ROOT / "configs" / "scenarios" / "p1-sandbox-5step-langgraph.yaml"
    config = ScenarioConfig.from_yaml(path)
    assert config.agent.framework == "langgraph"


def test_validate_docker_scenario_config() -> None:
    config = ScenarioConfig.model_validate(
        {
            "experiment_id": "p1-sandbox-docker",
            "agent": {
                "framework": "docker",
                "model": "local/docker-agent:test",
                "goal": "Run the dockerized agent.",
                "system_prompt": "Emit RedSentinel JSONL events.",
                "framework_config": {"docker_image": "local/docker-agent:test"},
            },
        }
    )

    assert config.agent.framework == "docker"
    assert config.agent.framework_config == {"docker_image": "local/docker-agent:test"}


def test_cassette_path_resolution() -> None:
    path = ROOT / "configs" / "scenarios" / "p1-sandbox-5step-direct-api.yaml"
    config = ScenarioConfig.from_yaml(path)
    cassette = ROOT / "tests" / "fixtures" / "cassettes" / "direct_api" / config.experiment_id / "seed_42.yaml"
    assert cassette.exists()
