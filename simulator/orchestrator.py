import asyncio
from datetime import datetime

state = {
    "solar_kw": None,
    "battery_soc": None,
    "load_kw": None,
    "grid_carbon_intensity": None,
    "timestamps": {}
}

def is_fresh(ts, max_age):
    return (datetime.utcnow() - ts).seconds < max_age

async def orchestrator(queue, output_queue):
    while True:
        msg = await queue.get()

        src = msg["source"]
        state["timestamps"][src] = msg["timestamp"]

        if src == "solar":
            state["solar_kw"] = msg["solar_kw"]
            state["battery_soc"] = msg["battery_soc"]

        elif src == "load":
            state["load_kw"] = msg["load_kw"]

        elif src == "carbon":
            state["grid_carbon_intensity"] = msg["grid_carbon_intensity"]

        if all(state[k] is not None for k in [
            "solar_kw", "battery_soc", "load_kw", "grid_carbon_intensity"
        ]):
            telemetry = {
                "timestamp": datetime.utcnow().isoformat(),
                "solar_kw": state["solar_kw"],
                "battery_soc": state["battery_soc"],
                "load_kw": state["load_kw"],
                "grid_carbon_intensity": state["grid_carbon_intensity"],
                "quality": {
                    "solar": "fresh" if is_fresh(state["timestamps"]["solar"], 90) else "stale",
                    "load": "fresh" if is_fresh(state["timestamps"]["load"], 60) else "stale",
                    "carbon": "fresh" if is_fresh(state["timestamps"]["carbon"], 600) else "stale"
                }
            }

            await output_queue.put(telemetry)
