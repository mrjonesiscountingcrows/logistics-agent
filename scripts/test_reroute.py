"""
Test script: runs propose_reroute on a route's current (disrupted) stop
order and prints whether it found an improvement.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import select
from src.data.db import get_session
from src.models import Stop
from src.tools.reroute import propose_reroute


def run(route_id: int):
    with get_session() as session:
        stops = session.exec(
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence)
        ).all()

        if not stops:
            print(f"No stops found for route {route_id}.")
            return

        start_time = stops[0].window_start
        result = propose_reroute(stops, start_time)

        print(f"Baseline: {result['baseline_score']} of {len(stops)} stops on time")
        print(f"Best found: {result['best_score']} of {len(stops)} stops on time")

        if result["improved"]:
            print("\nImprovement found. Proposed new order:")
            for i, stop in enumerate(result["proposed_order"]):
                print(f"  {i}: Stop {stop.id} ({stop.address})")
        else:
            print("\nNo improvement found with local reshuffling.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_reroute.py <route_id>")
        sys.exit(1)
    run(int(sys.argv[1]))