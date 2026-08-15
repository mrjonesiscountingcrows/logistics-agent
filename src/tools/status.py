"""
Turns a route's current state into plain-English text for the model to
reason over, and a tool wrapper the model can call to get it.
"""
from src.tools.evaluate import evaluate_stop_order


def describe_route_status(stops: list, start_time) -> str:
    """
    Returns a human-readable summary of a route: which stops are on time,
    which are delayed, and by how much. This is what the model sees -
    not raw database rows.
    """
    result = evaluate_stop_order(stops, start_time)

    lines = [
        f"Route status: {result['on_time_count']} of {result['total_stops']} stops on time.",
        "",
    ]

    for stop, eta, is_on_time in result["stop_etas"]:
        status_text = "ON TIME" if is_on_time else "MISSED WINDOW"
        delay_note = f" (disrupted, +{stop.extra_delay_minutes} min)" if stop.extra_delay_minutes > 0 else ""
        lines.append(
            f"Stop {stop.id} ({stop.address}): ETA {eta.strftime('%H:%M')}, "
            f"window {stop.window_start.strftime('%H:%M')}-{stop.window_end.strftime('%H:%M')}, "
            f"{status_text}{delay_note}"
        )

    return "\n".join(lines)