import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.pricehubble.com/api/v1"

_token_cache = {"access_token": None, "expires_at": 0}


def authenticate():
    """Authenticate with PriceHubble and cache the access token (12h validity)."""
    cached = _token_cache
    if cached["access_token"] and time.time() < cached["expires_at"]:
        return cached["access_token"]

    username = os.getenv("PRICEHUBBLE_USERNAME")
    password = os.getenv("PRICEHUBBLE_PASSWORD")
    if not username or not password:
        raise ValueError(
            "PRICEHUBBLE_USERNAME and PRICEHUBBLE_PASSWORD must be set in .env"
        )

    resp = requests.post(
        f"{API_BASE}/auth/login",
        json={"username": username, "password": password},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    _token_cache["access_token"] = data["access_token"]
    # Cache for 11.5 hours to avoid edge-case expiry
    _token_cache["expires_at"] = time.time() + 11.5 * 3600

    return data["access_token"]


def valuate(properties, country_code="CH", deal_type="sale", valuation_dates=None):
    """Call PriceHubble Property Valuation API.

    Args:
        properties: list of property dicts (location, buildingYear, livingArea, etc.)
        country_code: ISO country code (CH, DE, AT, FR, etc.)
        deal_type: "sale" or "rent"
        valuation_dates: list of date strings (YYYY-MM-DD), one per property.
                         Defaults to today for each property.

    Returns:
        list of valuation result dicts
    """
    if valuation_dates is None:
        from datetime import date

        today = date.today().isoformat()
        valuation_dates = [today] * len(properties)

    all_valuations = []
    batch_size = 50

    for i in range(0, len(properties), batch_size):
        batch_props = properties[i : i + batch_size]
        batch_dates = valuation_dates[i : i + batch_size]
        result = _valuate_batch(batch_props, batch_dates, country_code, deal_type)
        all_valuations.extend(result)

    return all_valuations


def _valuate_batch(properties, valuation_dates, country_code, deal_type, retry=True):
    """Send a single batch (max 50) to the valuation endpoint."""
    token = authenticate()

    payload = {
        "dealType": deal_type,
        "valuationInputs": [
            {"property": prop, "valuationDate": vdate}
            for prop, vdate in zip(properties, valuation_dates)
        ],
        "countryCode": country_code,
    }

    resp = requests.post(
        f"{API_BASE}/valuation/property_value",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )

    if resp.status_code == 401 and retry:
        # Token expired — clear cache and retry once
        _token_cache["access_token"] = None
        _token_cache["expires_at"] = 0
        return _valuate_batch(
            properties, valuation_dates, country_code, deal_type, retry=False
        )

    resp.raise_for_status()
    data = resp.json()
    return data.get("valuations", [])
