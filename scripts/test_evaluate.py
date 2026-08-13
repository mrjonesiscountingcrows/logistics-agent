"""
Test script: runs evaluate_stop_order on a route's CURRENT stop order
(as it already sits in the database, including any disruption you injected)
and prints how many stops are on time.

This gives us the "baseline" number - once propose_reroute exists, we'll
compare its proposed order's score against this baseline to see if it's
actually an improvement.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import select
from src.data.db import get_session
from src.models import Stop
from src.tools.evaluate import evaluate_stop_order


def run(route_id: int):
    with get_session() as session:
        stops = session.exec(
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence)
        ).all()

        if not stops:
            print(f"No stops found for route {route_id}.")
            return

        start_time = stops[0].window_start
        result = evaluate_stop_order(stops, start_time)

        print(f"Route {route_id}: {result['on_time_count']} of {result['total_stops']} stops on time\n")
        for stop, eta, on_time in result["stop_etas"]:
            flag = "ON TIME" if on_time else "MISSED WINDOW"
            print(f"  Stop {stop.id} ({stop.address}): ETA {eta.strftime('%H:%M')} - {flag}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_evaluate.py <route_id>")
        sys.exit(1)
    run(int(sys.argv[1]))
