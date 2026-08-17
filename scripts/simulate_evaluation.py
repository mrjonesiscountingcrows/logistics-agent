"""
Phase 5: runs the disruption -> reroute cycle across many simulated days,
comparing baseline (no intervention) vs. agent-proposed reroute, to get a
real measured improvement instead of a single manual test.

This calls propose_reroute directly, not the full LLM loop - Phase 4
already proved the model reliably invokes the right tool at the right
time, so this phase is about measuring how good the underlying reroute
logic is, not testing the model's judgment again.
"""
import sys
import os
import random
import time
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import select
from src.data.db import get_session
from src.models import Stop
from src.tools.evaluate import evaluate_stop_order
from src.tools.reroute import propose_reroute

NUM_SIMULATED_DAYS = 10
NUM_STOPS_TO_DISRUPT = 5
MIN_DELAY_MINUTES = 20
MAX_DELAY_MINUTES = 90


def reset_stops(stops):
    """Clears any disruption, back to a clean baseline - same idea as
    regenerate_windows.py, but only resets status, not the windows
    themselves (those stay fixed across all simulated days)."""
    with get_session() as session:
        for stop in stops:
            stop.extra_delay_minutes = 0
            stop.status = "pending"
            session.add(stop)
        session.commit()


def disrupt_stops(stops):
    """Same logic as inject_disruption.py, reused here so each simulated
    day gets a fresh, randomized problem to solve."""
    affected = random.sample(stops, min(NUM_STOPS_TO_DISRUPT, len(stops)))
    with get_session() as session:
        for stop in affected:
            stop.extra_delay_minutes = random.randint(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)
            stop.status = "delayed"
            session.add(stop)
        session.commit()


def run_simulation(route_id: int):
    with get_session() as session:
        stops = session.exec(
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence)
        ).all()

    if not stops:
        print(f"No stops found for route {route_id}.")
        return

    start_time = stops[0].window_start

    baseline_scores = []
    reroute_scores = []

    for day in range(1, NUM_SIMULATED_DAYS + 1):
        reset_stops(stops)
        disrupt_stops(stops)

        # reload stops fresh from the DB so we're evaluating the disrupted state
        with get_session() as session:
            stops = session.exec(
                select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence)
            ).all()

        baseline_result = evaluate_stop_order(stops, start_time)
        baseline_scores.append(baseline_result["on_time_count"])

        reroute_result = propose_reroute(stops, start_time)
        reroute_scores.append(reroute_result["best_score"])

        print(
            f"Day {day:2d}: baseline {baseline_result['on_time_count']:2d}/30  ->  "
            f"with reroute {reroute_result['best_score']:2d}/30"
        )

        time.sleep(1)  # be polite to the free ORS API rate limit

    avg_baseline = sum(baseline_scores) / len(baseline_scores)
    avg_reroute = sum(reroute_scores) / len(reroute_scores)

    print("\n=== Results across {} simulated days ===".format(NUM_SIMULATED_DAYS))
    print(f"Average baseline on-time:      {avg_baseline:.1f} / 30")
    print(f"Average with reroute applied:  {avg_reroute:.1f} / 30")
    print(f"Average improvement:           {avg_reroute - avg_baseline:+.1f} stops")
    print(f"Best baseline day:             {max(baseline_scores)} / 30")
    print(f"Worst baseline day:            {min(baseline_scores)} / 30")
    print(f"Best reroute day:               {max(reroute_scores)} / 30")
    print(f"Worst reroute day:              {min(reroute_scores)} / 30")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/simulate_evaluation.py <route_id>")
        sys.exit(1)
    run_simulation(int(sys.argv[1]))