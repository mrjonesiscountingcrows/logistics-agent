"""
Tool: routing. Narrow, single-purpose wrapper around OpenRouteService.

Phase 0/1 scope: geocode addresses, get drive time between two points, get
an ordered route across multiple stops. No agent logic here - this should
run standalone from a plain script and return sane output before it's ever
called from a loop.
"""
import os
import openrouteservice
from dotenv import load_dotenv

load_dotenv()

_client = openrouteservice.Client(key=os.getenv("ORS_API_KEY"))


def geocode(address: str) -> tuple[float, float]:
    """
    Returns (lat, lon) for a real address.

    Uses Nominatim (OpenStreetMap's free geocoder, no API key required)
    instead of ORS's geocode endpoint. ORS is still used for routing/drive
    times below - only geocoding is routed elsewhere, since it's a
    single independent tool call and doesn't need to be ORS specifically.
    """
    import requests
    import time

    resp = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": address, "format": "json", "limit": 1},
        headers={"User-Agent": "logistics-agent-learning-project"},
    )
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"No geocoding result for address: {address}")
    time.sleep(1)  # Nominatim's usage policy: max 1 request/second
    return float(results[0]["lat"]), float(results[0]["lon"])


def get_drive_time_seconds(origin: tuple[float, float], dest: tuple[float, float]) -> float:
    """Real drive time between two (lat, lon) points, in seconds."""
    # ORS expects (lon, lat) ordering
    coords = [(origin[1], origin[0]), (dest[1], dest[0])]
    result = _client.directions(coords, profile="driving-car", format="geojson")
    return result["features"][0]["properties"]["summary"]["duration"]


def get_route_legs(stops: list[tuple[float, float]]) -> list[float]:
    """
    Given an ordered list of (lat, lon) stops, returns the drive time in
    seconds for EACH leg of the trip (stop 1 -> stop 2, stop 2 -> stop 3,
    etc). This is different from get_drive_time_seconds (one pair only) and
    get_route_order (total trip time only) - this is the piece needed to
    calculate an arrival time at every individual stop along the route.

    Returns a list one shorter than the stops list, e.g. 5 stops -> 4 legs.
    """
    coords = [(lon, lat) for lat, lon in stops]
    result = _client.directions(coords, profile="driving-car", format="geojson")
    segments = result["features"][0]["properties"]["segments"]
    return [segment["duration"] for segment in segments]


def get_route_order(stops: list[tuple[float, float]]) -> dict:
    """
    Given an ordered list of (lat, lon) stops, returns the full route geometry
    and total duration/distance from ORS. Does NOT optimize stop order -
    that's what propose_reroute() will do in Phase 1, using this as a
    building block.
    """
    coords = [(lon, lat) for lat, lon in stops]
    result = _client.directions(coords, profile="driving-car", format="geojson")
    summary = result["features"][0]["properties"]["summary"]
    return {
        "duration_seconds": summary["duration"],
        "distance_meters": summary["distance"],
        "raw": result,
    }
