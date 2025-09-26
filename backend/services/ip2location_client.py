from __future__ import annotations

import os
import math
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict
import requests


# Load airport data
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "airports.json"
AIRPORTS: list[dict] = json.loads(DATA_PATH.read_text(encoding="utf-8"))

# Helpers
_COUNTRY_ALIASES = {
    "united states of america": "united states",
    "usa": "united states",
    "us": "united states",
    "united kingdom of great britain and northern ireland": "united kingdom",
    "uk": "united kingdom",
    "great britain": "united kingdom",
    "gb": "united kingdom",
    "uae": "united arab emirates",
    "republic of ireland": "ireland",
    "korea, republic of": "south korea",
    "republic of korea": "south korea",
    "czechia": "czech republic",
}

def _norm_country(name: str) -> str:
    s = (name or "").strip().lower()
    return _COUNTRY_ALIASES.get(s, s)

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    p = math.pi / 180.0
    a = (
        0.5 - math.cos((lat2 - lat1) * p) / 2
        + math.cos(lat1 * p) * math.cos(lat2 * p) * (1 - math.cos((lon2 - lon1) * p)) / 2
    )
    return 2 * R * math.asin(math.sqrt(a))

def _infer_ip_version(ip: str) -> int:
    return 6 if ":" in ip else 4

def _clean_airport(ap: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalize one airport record once at load time."""
    if ap.get("latitude") is None or ap.get("longitude") is None:
        return None
    try:
        lat = float(ap["latitude"])
        lon = float(ap["longitude"])
    except (TypeError, ValueError):
        return None

    return {
        "airport": ap.get("airport"),
        "city": ap.get("city"),
        "country": ap.get("country"),
        "iata": ap.get("iata_code") or ap.get("iata"),
        "lat": lat,
        "lon": lon,
    }


# Pre-index airports by normalized country
_AIRPORTS_BY_COUNTRY: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

for raw in AIRPORTS:
    cleaned = _clean_airport(raw)
    if not cleaned:
        continue
    c = _norm_country(cleaned.get("country", ""))
    if not c:
        continue
    _AIRPORTS_BY_COUNTRY[c].append(cleaned)

# Freeze lists so they can’t be accidentally mutated later
for k, v in list(_AIRPORTS_BY_COUNTRY.items()):
    _AIRPORTS_BY_COUNTRY[k] = tuple(v)


# Core lookups
def _nearest_airport_in_country(
    user_lat: float,
    user_lon: float,
    user_country: str,
) -> Optional[Dict[str, Any]]:
    """Return standardized airport dict + distance_km, or None if no match."""
    candidates = _AIRPORTS_BY_COUNTRY.get(_norm_country(user_country))
    if not candidates:
        return None

    best = None
    best_d = None
    for ap in candidates:
        d = _haversine_km(user_lat, user_lon, ap["lat"], ap["lon"])
        if best_d is None or d < best_d:
            best_d = d
            best = ap

    if not best:
        return None

    return {**best, "distance_km": round(best_d, 2)}

def _resolve_ip(ip_address: str) -> Dict[str, Any]:
    """Resolve user geolocation from IP (uses IP2Location if available)."""
    api_key = os.getenv("IP2LOCATION_API_KEY")

    # Defaults if API missing or fails
    city = "London"
    region = "England"
    country = "United Kingdom"
    lat = 51.5074
    lon = -0.1278
    ip_ver = _infer_ip_version(ip_address)
    ip_out = ip_address

    if api_key:
        try:
            resp = requests.get(
                "https://api.ip2location.io/",
                params={"key": api_key, "ip": ip_address, "format": "json"},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json() or {}
            city = data.get("city_name") or city
            region = data.get("region_name") or region
            country = data.get("country_name") or country
            lat = float(data.get("latitude") or lat)
            lon = float(data.get("longitude") or lon)
            ip_out = data.get("ip") or ip_out
            ip_ver = int(data.get("version") or ip_ver)
        except requests.RequestException:
            # optionally log here
            pass

    return {
        "user_city": city,
        "user_region": region,
        "user_country": country,
        "user_latitude": float(lat),
        "user_longitude": float(lon),
        "ip_version": ip_ver,
        "user_ip": ip_out,
    }

def resolve_user_and_nearest(ip: str) -> Dict[str, Any]:
    """Resolve user from IP, then pick the nearest airport in the same country."""
    user = _resolve_ip(ip)
    nearest = _nearest_airport_in_country(
        user_lat=user["user_latitude"],
        user_lon=user["user_longitude"],
        user_country=user["user_country"],
    )
    return {**user, "nearest_airport": nearest}
