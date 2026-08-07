import pytest

from src.agents.trader import SAFE_TRADE_TOOLS
from src.crew import TradePlan, sanitize_query


def test_sanitize_query_normalizes_whitespace():
    assert sanitize_query("  Analyze ETH  ") == "Analyze ETH"


@pytest.mark.parametrize("query", ["", "   "])
def test_sanitize_query_rejects_empty_input(query):
    with pytest.raises(ValueError, match="must not be empty"):
        sanitize_query(query)


def test_trade_plan_defaults_to_unexecuted_and_needs_approval():
    plan = TradePlan(summary="No action yet")
    assert plan.approval_required is True
    assert plan.executed is False


def test_trade_planner_has_no_live_execution_tool():
    names = {tool.name.lower() for tool in SAFE_TRADE_TOOLS}
    assert "execute managed swap" not in names
    assert "simulate swap" in names
    assert "prepare unsigned swap" in names

