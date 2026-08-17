"""
Skills: fixed, named recipes built from tools already proven in the
harness. A skill doesn't add new capability - it packages a known-good
sequence of existing tool calls so the model can invoke it as one action
instead of reasoning through the same steps every time.
"""
from sqlmodel import select

from src.data.db import get_session
from src.models import Stop, DecisionLogEntry
from src.agent.harness import execute_tool_with_guardrails


def _log_skill_invocation(route_id: int, reasoning: str, outcome: str):
    with get_session() as session:
        entry = DecisionLogEntry(
            route_id=route_id,
            trigger="disruption_response_skill",
            reasoning=reasoning,
            action_taken="skill_invoked",
            outcome=outcome[:300],
        )
        session.add(entry)
        session.commit()


def run_disruption_response(route_id: int) -> str:
    """
    The disruption_response skill: check the route, and if any stops have
    missed their window, propose a reroute automatically. Both steps still
    go through the harness - this just decides WHEN to trigger them,
    instead of leaving that decision to the model each time.
    """
    status_result = execute_tool_with_guardrails(
        "check_route_status", {"route_id": route_id}
    )

    has_missed_window = "MISSED WINDOW" in status_result

    if not has_missed_window:
        outcome = "No missed windows found. No reroute needed."
        _log_skill_invocation(route_id, reasoning="Checked status, all stops on time",
                               outcome=outcome)
        return f"{status_result}\n\n{outcome}"

    reroute_result = execute_tool_with_guardrails(
        "propose_reroute", {"route_id": route_id}
    )

    outcome = f"Missed windows found. Reroute check:\n{reroute_result}"
    _log_skill_invocation(route_id, reasoning="Checked status, missed windows found, checked for a reroute",
                           outcome=outcome)

    return f"{status_result}\n\n{outcome}"