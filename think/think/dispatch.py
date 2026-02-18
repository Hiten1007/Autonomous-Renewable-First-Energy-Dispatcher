from fastapi import APIRouter
from llmcontroller import run_mcp_agent_flow
from think.sense.data_orchestrator import build_llm_context
from datetime import datetime
from think.services.strategy_select import run_deterministic_math, extract_strategy_from_output
from think.helpers.update_state import update_battery_state_local_json as update_state
import threading
import json
import time
from pathlib import Path
from think.services.svc_safe_throttle import execute_safe_throttle
from types import SimpleNamespace

router = APIRouter(prefix="/dispatch", tags=["dispatch"])

# Path to your local JSON
LOCAL_JSON = Path("dispatch_data.json")

# Global thread state
_dispatch_thread = None
_dispatch_running = False

def dispatch_loop():
    global _dispatch_running
    _dispatch_running = True

    while _dispatch_running:
        try:
            now = datetime.now()
            telemetry_data = build_llm_context(now)

            agent_raw_output = run_mcp_agent_flow(telemetry_data)
            strategy_intent = extract_strategy_from_output(agent_raw_output)

            strategy_name = (
                strategy_intent.get("strategy", "SVC_SAFE_THROTTLE")
                if strategy_intent else "SVC_SAFE_THROTTLE"
            )

            dispatch_math = run_deterministic_math(strategy_name, telemetry_data)

            # update battery state
            update_state(
                dispatch_math["battery"]["soc_after_mwh"],
                telemetry_data["current_state"]["battery"]["capacity_mwh"]
            )

            normal_output = execute_safe_throttle(
    SimpleNamespace(
        solar=dispatch_math["solar"]["generated_mwh"],
        load=dispatch_math["supply_mix"]["local_renewables_mwh"]
             + dispatch_math["supply_mix"]["grid_import_mwh"],
        battery_energy=dispatch_math["battery"]["soc_after_mwh"]
    )
)
            normal_carbon_saved = normal_output['carbon']['saved_kgco2']
            final_response = {
                "meta": {
                    "timestamp": telemetry_data["metadata"]["trigger_timestamp"],
                    "region": telemetry_data["metadata"]["region"],
                    "window_minutes": 30
                },
                "solar": dispatch_math["solar"],
                "battery": dispatch_math["battery"],
                "supply_mix": dispatch_math["supply_mix"],
                "carbon": dispatch_math["carbon"],
                "normal_carbon_saved": normal_carbon_saved,
                "strategy_intent": strategy_intent,
                "summary": f"Executed {strategy_name}"
            }

            # add battery update logic

            # load existing file
            history = []
            if LOCAL_JSON.exists():
                with open(LOCAL_JSON, "r") as f:
                    history = json.load(f)

            history.append(final_response)
            history = history[-100:]  # keep last 100

            with open(LOCAL_JSON, "w") as f:
                json.dump(history, f, indent=2)

            print("✅ Dispatch updated")

        except Exception as e:
            print("❌ Dispatch loop error:", e)

        time.sleep(30 * 60)


@router.post("/")
def dispatch():
    global _dispatch_thread, _dispatch_running

    if LOCAL_JSON.exists():
        with open(LOCAL_JSON, "r") as f:
            current_data = json.load(f)
    else:
        current_data = []

    if not _dispatch_running:
        _dispatch_thread = threading.Thread(
            target=dispatch_loop,
            daemon=True
        )
        _dispatch_thread.start()

    # ✅ MATCH FRONTEND EXPECTATION
    return {
        "status": "success",
        "source": "local",
        "data": current_data
    }



@router.get("/history")
def history():
    if LOCAL_JSON.exists():
        with open(LOCAL_JSON, "r") as f:
            return json.load(f)
    return []
