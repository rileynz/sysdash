"""Weather fetching via wttr.in.

No API key required. Falls back gracefully (returns None) on any
network failure so a flaky connection never crashes the dashboard -
the weather panel just shows "unavailable" and the rest of the UI
keeps working.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

WTTR_TIMEOUT_SECONDS = 5


@dataclass
class WeatherSnapshot:
    location: str
    temp_c: float
    feels_like_c: float
    condition: str
    icon: str  # tabler-style icon hint, used by the UI to pick a glyph


# Rough condition -> icon-class mapping. wttr.in gives free-text conditions
# so this is intentionally a substring match, not an exhaustive enum.
_ICON_MAP = [
    (("sunny", "clear"), "sun"),
    (("partly cloudy",), "cloud-sun"),
    (("cloudy", "overcast"), "cloud"),
    (("rain", "drizzle", "shower"), "cloud-rain"),
    (("thunder",), "cloud-bolt"),
    (("snow", "sleet", "ice"), "snowflake"),
    (("fog", "mist", "haze"), "haze"),
]


def _pick_icon(condition: str) -> str:
    lowered = condition.lower()
    for keywords, icon in _ICON_MAP:
        if any(k in lowered for k in keywords):
            return icon
    return "cloud"


def fetch_weather(location: str = "") -> WeatherSnapshot | None:
    """Fetch current weather. Empty location lets wttr.in geolocate by IP.

    Returns None on any failure (network down, malformed response, etc.)
    rather than raising - the UI treats None as "show unavailable".
    """
    url = f"https://wttr.in/{location}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
        with urllib.request.urlopen(req, timeout=WTTR_TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        current = data["current_condition"][0]
        nearest = data.get("nearest_area", [{}])[0]
        area_name = nearest.get("areaName", [{}])[0].get("value", "unknown")

        condition_text = current["weatherDesc"][0]["value"]

        return WeatherSnapshot(
            location=area_name,
            temp_c=float(current["temp_C"]),
            feels_like_c=float(current["FeelsLikeC"]),
            condition=condition_text,
            icon=_pick_icon(condition_text),
        )
    except (
        urllib.error.URLError,
        TimeoutError,
        KeyError,
        IndexError,
        ValueError,
        json.JSONDecodeError,
    ):
        return None
