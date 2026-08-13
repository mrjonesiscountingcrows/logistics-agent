"""
Regenerates delivery windows for an existing route's stops, based on real
drive times instead of an arbitrary fixed schedule. This gives us a
baseline where the undisrupted route can actually succeed, so that
disruption + reroute testing means something.
"""
import sys
import os
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import select
from src.data.db import get_session
from src.models import Stop
from src.tools.routing import get_route_legs

# how much buffer to give each stop on either side of its real arrival time
WINDOW_BUFFER_MINUTES = 45


def regenerate_windows(route_id: int):
    with get_session() as session:
        stops = session.exec(
            select(Stop).where(Stop.route_id == route_id).order_by(Stop.sequence)
        ).all()

        if not stops:
            print(f"No stops found for route {route_id}.")
            return

        coords = [(stop.lat, stop.lon) for stop in stops]
        leg_durations = get_route_legs(coords)  # real seconds between each pair

        # first stop keeps a window starting at its original window_start
        current_time = stops[0].window_start
        buffer = timedelta(minutes=WINDOW_BUFFER_MINUTES)

        stops[0].window_start = current_time - buffer
        stops[0].window_end = current_time + buffer
        stops[0].planned_eta = None
        stops[0].status = "pending"
        stops[0].extra_delay_minutes = 0
        session.add(stops[0])

        for i, leg_seconds in enumerate(leg_durations):
            current_time = current_time + timedelta(seconds=leg_seconds)
            stop = stops[i + 1]
            stop.window_start = current_time - buffer
            stop.window_end = current_time + buffer
            stop.planned_eta = None
            stop.status = "pending"
            stop.extra_delay_minutes = 0
            session.add(stop)

        session.commit()
        print(f"Regenerated windows for {len(stops)} stops on route {route_id}, "
              f"based on real drive times with a {WINDOW_BUFFER_MINUTES}-minute buffer.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/regenerate_windows.py <route_id>")
        sys.exit(1)
    regenerate_windows(int(sys.argv[1]))