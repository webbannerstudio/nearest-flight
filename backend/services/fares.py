import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Path to flights data
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "flights.json"

def _load_pricing_map() -> Optional[dict]:
    # Load JSON pricing map
    if not DATA_PATH.exists():
        return None
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _select_entry_for_origin(pricing_map: dict, origin_iata: str) -> Optional[Dict[str, Any]]:
    # Find first valid entry for origin
    data = (pricing_map or {}).get("data", {})
    if not isinstance(data, dict) or not data:
        return None

    origin = origin_iata.strip().upper()
    for key, v in data.items():
        if key.startswith(f"{origin}-") and isinstance(v, dict) and "price" in v and "currency" in v and "error" not in v:
            return v
    return None

def get_flight_for_origin(origin_iata: str) -> Optional[dict]:
    # Public lookup by origin
    pricing = _load_pricing_map()
    if not pricing:
        return None
    return _select_entry_for_origin(pricing, origin_iata)

def as_live_flight_object(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # Convert raw entry into API format
    if not raw:
        return None

    currency = raw.get("currency") or "USD"
    price = raw.get("price") or 0
    display_price = raw.get("display_price") or f"{currency}{price}"
    date_only = raw.get("date") or datetime.utcnow().date().isoformat()

    return {
        "origin_name": raw.get("origin_name"),
        "origin_city": raw.get("origin_city"),
        "origin_country": raw.get("origin_country"),
        "origin_iata_code": raw.get("origin"),
        "destination_city": raw.get("destination_city"),
        "destination_name": raw.get("destination_name"),
        "destination_iata_code": raw.get("destination"),
        "price": price,
        "display_price": display_price,
        "currency": currency,
        "flight_date": date_only,
    }

def prices_updated_iso() -> str:
    # Last modified time of data file
    if not DATA_PATH.exists():
        return datetime.utcnow().isoformat() + "Z"
    ts = datetime.utcfromtimestamp(DATA_PATH.stat().st_mtime)
    return ts.isoformat() + "Z"
