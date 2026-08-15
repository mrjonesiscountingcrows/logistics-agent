"""
The harness: guardrails, decision logging, and error handling wrapped
around every tool call the agent makes.

The loop no longer calls tool functions directly - it calls
execute_tool_with_guardrails() here, which does the real work AND writes
an audit trail entry for it, using the DecisionLogEntry table that's
existed since Phase 0 but was never actually used until now.
"""
from datetime import datetime, date
from sqlmodel import select

from src.data.db import get_session
from src.models import Stop, DecisionLogEntry
from src.tools.status import describe_route_status
from src.tools.reroute import propose_reroute as run_propose_reroute

MAX_REROUTES_PER_ROUTE_PER_DAY = 3


def _load_stops(route_id: int):
    with get_session() as session:
        stops = session.exec(
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence)
        ).all()
    return stops


def _count_reroutes_today(route_id: int) -> int:
    """Guardrail check: how many reroutes have already been proposed today."""
    with get_session() as session:
        today_start = datetime.combine(date.today(), datetime.min.time())
        entries = session.exec(
            select(DecisionLogEntry).where(
                DecisionLogEntry.route_id == route_id,
                DecisionLogEntry.action_taken == "reroute_proposed",
                DecisionLogEntry.timestamp >= today_start,
            )
        ).all()
        return len(entries)


def _log_decision(route_id: int, trigger: str, reasoning: str, action_taken: str, outcome: str = None):
    with get_session() as session:
        entry = DecisionLogEntry(
            route_id=route_id,
            trigger=trigger,
            reasoning=reasoning,
            action_taken=action_taken,
            outcome=outcome,
        )
        session.add(entry)
        session.commit()


def execute_tool_with_guardrails(tool_name: str, arguments: dict) -> str:
    """
    Every tool call the model makes goes through here. This is the harness
    layer: it enforces the daily reroute limit, logs what happened and why,
    and catches errors so a bad tool call doesn't crash the whole run.
    """
    route_id = arguments["route_id"]

    try:
        stops = _load_stops(route_id)
        if not stops:
            result = f"No stops found for route {route_id}."
            _log_decision(route_id, trigger=tool_name, reasoning="No stops found",
                           action_taken="error", outcome=result)
            return result

        start_time = stops[0].window_start

        if tool_name == "check_route_status":
            result = describe_route_status(stops, start_time)
            _log_decision(route_id, trigger="check_route_status",
                           reasoning="Agent checked route status",
                           action_taken="status_checked", outcome=result[:200])
            return result

        elif tool_name == "propose_reroute":
            reroutes_today = _count_reroutes_today(route_id)

            if reroutes_today >= MAX_REROUTES_PER_ROUTE_PER_DAY:
                result = (
                    f"Reroute limit reached: {reroutes_today} reroutes already proposed "
                    f"for this route today (max {MAX_REROUTES_PER_ROUTE_PER_DAY}). "
                    f"Flagging for human review instead of proposing another."
                )
                _log_decision(route_id, trigger="propose_reroute_blocked",
                               reasoning="Daily reroute limit reached",
                               action_taken="flagged_for_review", outcome=result)
                return result

            reroute_result = run_propose_reroute(stops, start_time)
            lines = [
                f"Baseline: {reroute_result['baseline_score']} of {len(stops)} stops on time.",
                f"Best found: {reroute_result['best_score']} of {len(stops)} stops on time.",
            ]
            if reroute_result["improved"]:
                lines.append("Proposed new stop order (not applied):")
                for i, stop in enumerate(reroute_result["proposed_order"]):
                    lines.append(f"  {i}: Stop {stop.id} ({stop.address})")
                action = "reroute_proposed"
            else:
                lines.append("No improvement found.")
                action = "no_action"

            result = "\n".join(lines)
            _log_decision(
                route_id, trigger="propose_reroute",
                reasoning=f"Baseline {reroute_result['baseline_score']}, best {reroute_result['best_score']}",
                action_taken=action, outcome=result[:300],
            )
            return result

        else:
            result = f"Unknown tool: {tool_name}"
            _log_decision(route_id, trigger=tool_name, reasoning="Unrecognized tool call",
                           action_taken="error", outcome=result)
            return result

    except Exception as e:
        error_message = f"Tool execution failed: {str(e)}"
        _log_decision(route_id, trigger=tool_name, reasoning="Exception during tool execution",
                       action_taken="error", outcome=error_message)
        return error_message