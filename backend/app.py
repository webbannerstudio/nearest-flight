from pathlib import Path
from enum import Enum
from pydantic import IPvAnyAddress

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse

from .services.ip2location_client import resolve_user_and_nearest
from .services.fares import (
    get_flight_for_origin,
    as_live_flight_object,
    prices_updated_iso,
)

# Test locations for dropdown parameter
class TestLocation(str, Enum):
    bali           = "Bali"
    denmark        = "Denmark"
    germany        = "Germany"
    iceland        = "Iceland - no flight"
    india          = "India"
    ireland        = "Ireland"
    japan          = "Japan"
    spain          = "Spain"
    switzerland    = "Switzerland"
    united_kingdom = "United Kingdom"
    united_states  = "United States"

# Sample IPs mapped to locations
TEST_IP_MAP = {
    TestLocation.bali:           "202.180.53.34",
    TestLocation.denmark:        "93.176.79.132",
    TestLocation.germany:        "93.213.161.160",
    TestLocation.iceland:        "147.28.31.255",
    TestLocation.india:          "223.191.3.77",
    TestLocation.ireland:        "86.47.0.1",
    TestLocation.japan:          "152.69.193.86",
    TestLocation.spain:          "81.45.0.1",
    TestLocation.switzerland:    "194.230.159.87",
    TestLocation.united_kingdom: "81.2.69.160",
    TestLocation.united_states:  "52.162.161.148",
}

app = FastAPI(title="Nearest Flight API")

# Build user payload with key metadata
def _user_payload(user: dict) -> dict:
    return {
        "city": user["user_city"],
        "region": user["user_region"],
        "country": user["user_country"],
        "latitude": user["user_latitude"],
        "longitude": user["user_longitude"],
        "ip": user["user_ip"],
    }

@app.get("/", response_class=HTMLResponse)
def home():
    # Simple landing page with quick test links
    return """
    <h1>Nearest Flight API</h1>
    <p><a href="/docs">/docs</a></p>
    <ul>
      <li><a href="/api/nearest-flight?ip=223.191.3.77">IN test</a></li>
      <li><a href="/api/nearest-flight?ip=81.2.69.160">UK test</a></li>
      <li><a href="/api/nearest-flight?ip=52.162.161.148">US test</a></li>
    </ul>
    """

@app.get("/health")
def health():
    # Simple health check
    return {"status": "ok"}

@app.get("/api/nearest-flight")
def nearest_flight(
    request: Request,
    ip: IPvAnyAddress | None = Query(
        default=None,
        description="Enter a custom IP address to simulate user location"
    ),
    location: TestLocation | None = Query(
        default=None,
        description="Or pick a sample test location"
    ),
):
    # Precedence: custom IP > dropdown > client IP
    if ip is not None:
        caller_ip = str(ip)
    elif location is not None:
        caller_ip = TEST_IP_MAP[location]
    else:
        caller_ip = request.client.host or "0.0.0.0"

    # Resolve nearest airport for the user
    user = resolve_user_and_nearest(caller_ip)
    nearest = user["nearest_airport"]

    if nearest is None:
        # No matching airport → return message only
        return {
            "user": _user_payload(user),
            "nearest_airport": None,
            "flight": None,
            "message": f"No flights available from {user['user_country']}",
        }

    # Fetch cheapest flight for origin airport
    origin_code = nearest["iata"]
    raw = get_flight_for_origin(origin_code)

    if raw:
        # Build enriched flight object
        flight = as_live_flight_object(raw) or {}
        flight["prices_updated"] = prices_updated_iso()
        message = None
    else:
        flight = None
        message = f"No flights available from {nearest['country']}"

    # Return structured response
    return {
        "user": _user_payload(user),
        "nearest_airport": nearest,
        "flight": flight,
        "message": message,
    }
