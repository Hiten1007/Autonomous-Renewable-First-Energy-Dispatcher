
import requests
import csv
import os
from datetime import datetime
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = "cqfoNJvOGZcfiBcNPZs8"

if not API_KEY:
    print("❌ ERROR: API Key not found. Check your .env file.")
    exit(1)

ZONE = "IN-NO"
BASE_URL = "https://api.electricitymaps.com/v3"
HEADERS = {"auth-token": API_KEY}
OUTPUT_FILE = "north_india_grid_carbon_full_snapshot.csv"

def fetch(endpoint, params=None):
    try:
        r = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error {r.status_code}: {r.text}")
        raise e

def run_once():
    # Fetch all 3 required signals
    lifecycle_data = fetch("/carbon-intensity/latest", {"zone": ZONE})
    direct_data = fetch("/carbon-intensity/latest", {"zone": ZONE, "emissionFactorType": "direct"})
    power_data = fetch("/power-breakdown/latest", {"zone": ZONE})

    # Electricity Maps power-breakdown already provides these percentages
    re_pct = power_data.get('renewablePercentage')
    cfe_pct = power_data.get('fossilFreePercentage')

    row = {
        "timestamp": lifecycle_data["datetime"],
        "zone": ZONE,
        "ci_direct_gco2": direct_data["carbonIntensity"],
        "ci_lifecycle_gco2": lifecycle_data["carbonIntensity"],
        "renewable_pct": re_pct,
        "carbon_free_pct": cfe_pct,
        "is_estimated": lifecycle_data["isEstimated"]
    }

    # ---------- Pretty Table Output for your Dashboard ----------
    print("\n" + "="*45)
    print(f"🌍 GRID SNAPSHOT: {ZONE}")
    print(f"⏰ {row['timestamp']}")
    print("-" * 45)
    print(f"⚡ Carbon Intensity (Direct):    {row['ci_direct_gco2']} gCO₂/kWh")
    print(f"🌱 Carbon Intensity (Lifecycle): {row['ci_lifecycle_gco2']} gCO₂/kWh")
    print(f"♻️  Renewable Energy (RE%):      {row['renewable_pct']}%")
    print(f"⚛️  Carbon-Free Energy (CFE%):   {row['carbon_free_pct']}%")
    print("="*45 + "\n")

    # Save to CSV
    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

if __name__ == "__main__":
    run_once()