"""
Evaluates a proposed order of stops: walks through them in sequence, adds
up real drive time between each one, and checks whether the driver would
arrive within each stop's promised window.

This is the "how good is this order" piece. Both the current order and any
alternative order we generate later get scored the same way, so we can
compare them fairly.
"""
from datetime import datetime, timedelta
from src.tools.routing import get_route_legs


def evaluate_stop_order(stops: list, start_time: datetime) -> dict:
    """
    stops: a list of Stop objects, IN THE ORDER we want to evaluate
           (not necessarily their current database order - this lets us
           test alternative orderings later without touching the database)
    start_time: when the driver begins the route

    Returns a dict with:
      - on_time_count: how many stops would be reached within their window
      - total_stops: how many stops were evaluated
      - stop_etas: a list of (stop, calculated_eta, is_on_time) for detail
    """
    if len(stops) < 2:
        raise ValueError("Need at least 2 stops to calculate drive legs between them")

    coords = [(stop.lat, stop.lon) for stop in stops]
    leg_durations = get_route_legs(coords)  # seconds between each consecutive pair

    current_time = start_time
    stop_etas = []
    on_time_count = 0

    # first stop's ETA is the start time, plus any disruption delay at that stop
    first_stop = stops[0]
    current_time = current_time + timedelta(minutes=first_stop.extra_delay_minutes)
    is_on_time = first_stop.window_start <= current_time <= first_stop.window_end
    stop_etas.append((first_stop, current_time, is_on_time))
    if is_on_time:
        on_time_count += 1

    # every stop after that: add the real drive time for that leg, PLUS any
    # disruption delay at that specific stop. Because current_time carries
    # forward, a delay at one stop pushes back every stop that follows it -
    # same as it would in reality.
    for i, leg_seconds in enumerate(leg_durations):
        current_time = current_time + timedelta(seconds=leg_seconds)
        stop = stops[i + 1]
        current_time = current_time + timedelta(minutes=stop.extra_delay_minutes)
        is_on_time = stop.window_start <= current_time <= stop.window_end
        stop_etas.append((stop, current_time, is_on_time))
        if is_on_time:
            on_time_count += 1

    return {
        "on_time_count": on_time_count,
        "total_stops": len(stops),
        "stop_etas": stop_etas,
    }
