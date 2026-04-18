import requests
from dotenv import load_dotenv
import os

# ---------------- CONFIG ----------------
load_dotenv()

API_KEY = os.getenv("ELECTRICITY_MAPS_API_KEY")
BASE_URL = "https://api.electricitymaps.com/v3"

HEADERS = {
    "auth-token": API_KEY
}
# ---------------------------------------

def fetch(endpoint, params=None):
    r = requests.get(
        f"{BASE_URL}{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=10
    )
    r.raise_for_status()
    return r.json()

# ---------------- PUBLIC INTERFACE ----------------

def get_grid_metrics(region: str):
    """
    Returns grid carbon + mix metrics in orchestrator-ready format
    """

    lifecycle = fetch("/carbon-intensity/latest", {"zone": region})
    direct = fetch(
        "/carbon-intensity/latest",
        {"zone": region, "emissionFactorType": "direct"}
    )
    power = fetch("/power-breakdown/latest", {"zone": region})

    return {
        "carbon_intensity_direct_gco2_per_kwh": direct["carbonIntensity"],
        "carbon_intensity_lifecycle_gco2_per_kwh": lifecycle["carbonIntensity"],
        "renewable_percentage": power.get("renewablePercentage"),
        "carbon_free_percentage": power.get("fossilFreePercentage"),
        "is_estimated": lifecycle.get("isEstimated", False),
        "timestamp": lifecycle.get("datetime")
    }
