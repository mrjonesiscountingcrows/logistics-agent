"""
Disruption injector.

Picks a handful of stops from a route and pretends a delay happened to
them - pushes back their planned arrival time and marks them "delayed".
This exists purely to give us test data: without a delay in the database,
there is nothing for the future agent to detect or react to.

Run this any time you want to simulate "something went wrong today".
"""
import sys
import os
import random
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import select
from src.data.db import get_session
from src.models import Stop

# how many stops to disrupt, and how late (in minutes) each one runs
NUM_STOPS_TO_DISRUPT = 5
MIN_DELAY_MINUTES = 20
MAX_DELAY_MINUTES = 90


def inject_disruptions(route_id: int):
    with get_session() as session:
        stops = session.exec(
            select(Stop).where(Stop.route_id == route_id)
        ).all()

        if not stops:
            print(f"No stops found for route {route_id}. Check the route ID.")
            return

        # randomly choose which stops get hit by a "disruption"
        affected = random.sample(stops, min(NUM_STOPS_TO_DISRUPT, len(stops)))

        for stop in affected:
            delay_minutes = random.randint(MIN_DELAY_MINUTES, MAX_DELAY_MINUTES)

            stop.extra_delay_minutes = delay_minutes
            stop.status = "delayed"

            session.add(stop)

            print(
                f"Stop {stop.id} ({stop.address}): delayed by {delay_minutes} minutes."
            )

        session.commit()
        print(f"\nDisrupted {len(affected)} of {len(stops)} stops on route {route_id}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/inject_disruption.py <route_id>")
        print("Example: python scripts/inject_disruption.py 3")
        sys.exit(1)

    route_id = int(sys.argv[1])
    inject_disruptions(route_id)
