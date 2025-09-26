# Nearest Flight API

The Nearest Flight API demonstrates how location-based targeting can power online display advertisement, enabling one ad unit to serve personalised flight offers across multiple markets. This avoids the costly production of separate creatives for each region, currency, or campaign window.

It works by detecting a user’s location with IP2Location, finding the nearest airport in the same country, and returning a flight from a local pricing map. If the user’s country has no matching airports or no price available, the API responds with flight: null and a clear error message.

In a production scenario, you’d replace the sample data with live fares from an airline’s API or a public service like Sky-Scrapper on RapidAPI.  
For this demo, a static flights.json file is included to keep everything self-contained and easy to test.

---

## Features
- Detects user geolocation from IP address  
- Finds the nearest airport from the user’s country; returns the distance  
- Fare lookup from a pricing map keyed as <ORIGIN>-<DESTINATION> (e.g. LHR-AUH)  
- FastAPI app with interactive Swagger/OpenAPI docs at /docs  

---

## Quick start
```
1. Clone & create venv
   git clone https://github.com/webbannerstudio/nearest-flight.git

3. Install dependencies
   pip install -r requirements.txt

4. Configure environment
   cp .env.example .env

   Edit .env as needed:
   IP2LOCATION_API_KEY=...              # optional; fallback location = London, GB
   PRICING_MAP_PATH=backend/data/flights.json   # optional; default

5. Run the API
   uvicorn backend.app:app --reload

   Open:
   - Docs UI → http://localhost:8000/docs
   - Main endpoint → http://localhost:8000/api/nearest-flight
```
---

## Endpoints
```
GET /api/nearest-flight  
Returns the nearest airport (same country) and a matching flight from your pricing map.
```
---

## Pricing map format

The API expects a JSON object with keys like <ORIGIN>-<DEST>:

```
{
  "LHR-AUH": {
    "origin_iata": "LHR",
    "origin_name": "Heathrow Airport",
    "origin_city": "London",
    "origin_country": "GB",
    "destination_iata": "AUH",
    "destination_name": "Abu Dhabi International Airport",
    "destination_city": "Abu Dhabi",
    "destination_country": "AE",
    "date": "2025-11-01",
    "price": 486,
    "currency": "GBP",
    "display_price": "£486"
  }
}
```

---

## Try it quickly

Example test with Google’s public IP (8.8.8.8):

curl "http://localhost:8000/api/nearest-flight?ip=8.8.8.8"
