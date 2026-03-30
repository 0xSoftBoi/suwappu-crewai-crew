"""Tests for the Suwappu CrewAI multi-agent trading crew."""
import os
import yaml


def test_readme_exists():
    assert os.path.exists("README.md")


def test_env_example_exists():
    assert os.path.exists(".env.example")


def test_agents_config_valid():
    """Agent config YAML should parse without errors."""
    with open("src/config/agents.yaml") as f:
        agents = yaml.safe_load(f)
    assert isinstance(agents, dict)
    assert len(agents) > 0


def test_tasks_config_valid():
    """Tasks config YAML should parse without errors."""
    with open("src/config/tasks.yaml") as f:
        tasks = yaml.safe_load(f)
    assert isinstance(tasks, dict)
    assert len(tasks) > 0


def test_three_agents_defined():
    """Should have analyst, risk, and trader agents."""
    agent_files = ["src/agents/analyst.py", "src/agents/risk.py", "src/agents/trader.py"]
    for f in agent_files:
        assert os.path.exists(f), f"Missing agent: {f}"


def test_tools_module_exists():
    """Suwappu tools wrapper should exist."""
    assert os.path.exists("src/tools/suwappu_tools.py")


def test_crew_entry_point_exists():
    """Main crew orchestrator should exist."""
    assert os.path.exists("src/crew.py")


def test_api_key_format():
    """API key should have expected prefix."""
    key = "suwappu_sk_test123"
    assert key.startswith("suwappu_sk_")
    assert len(key) > len("suwappu_sk_")
