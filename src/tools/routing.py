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
    """Returns (lat, lon) for a real address."""
    result = _client.pelias_search(text=address)
    coords = result["features"][0]["geometry"]["coordinates"]  # [lon, lat]
    return coords[1], coords[0]


def get_drive_time_seconds(origin: tuple[float, float], dest: tuple[float, float]) -> float:
    """Real drive time between two (lat, lon) points, in seconds."""
    # ORS expects (lon, lat) ordering
    coords = [(origin[1], origin[0]), (dest[1], dest[0])]
    result = _client.directions(coords, profile="driving-car", format="geojson")
    return result["features"][0]["properties"]["summary"]["duration"]


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
