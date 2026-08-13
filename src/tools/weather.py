"""
Tool: weather. Single call, single purpose - current conditions for a zone.
This is the simplest possible disruption signal for Phase 1's
disruption_response skill.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

_API_KEY = os.getenv("OPENWEATHER_API_KEY")
_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_conditions(lat: float, lon: float) -> dict:
    """Returns current conditions relevant to delivery risk."""
    resp = requests.get(_BASE_URL, params={
        "lat": lat,
        "lon": lon,
        "appid": _API_KEY,
        "units": "imperial",
    })
    resp.raise_for_status()
    data = resp.json()
    return {
        "condition": data["weather"][0]["main"],  # e.g. "Rain", "Snow", "Clear"
        "description": data["weather"][0]["description"],
        "wind_mph": data["wind"]["speed"],
        "temp_f": data["main"]["temp"],
    }
