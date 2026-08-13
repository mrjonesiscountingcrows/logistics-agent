"""
Geocodes the addresses in seed_addresses.py, creates one Route with a
synthetic driver, and assigns each address a Stop with a fake delivery
window. Real coordinates and real drive times; the time windows and driver
are invented.
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.db import get_session, init_db
from src.data.seed_addresses import ADDRESSES
from src.models import Route, Stop
from src.tools.routing import geocode

DELIVERY_DAY = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)


def build_synthetic_route():
    init_db()
    with get_session() as session:
        route = Route(driver_name="Driver A", date=DELIVERY_DAY)
        session.add(route)
        session.commit()
        session.refresh(route)

        for i, address in enumerate(ADDRESSES):
            lat, lon = geocode(address)

            # fake but plausible delivery window: stops spread across the day
            window_start = DELIVERY_DAY + timedelta(minutes=30 * i)
            window_end = window_start + timedelta(hours=2)

            stop = Stop(
                route_id=route.id,
                address=address,
                lat=lat,
                lon=lon,
                sequence=i,
                window_start=window_start,
                window_end=window_end,
                priority=random.choice(["standard", "standard", "standard", "high"]),
            )
            session.add(stop)

        session.commit()
        print(f"Route {route.id} created with {len(ADDRESSES)} stops.")


if __name__ == "__main__":
    build_synthetic_route()
