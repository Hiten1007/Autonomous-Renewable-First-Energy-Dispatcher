from fastapi import APIRouter
from llmcontroller import run_mcp_agent_flow
from think.sense.data_orchestrator import build_llm_context
from datetime import datetime
from think.pydantic_classes import PhysicsSlice, CarbonSlice
from think.services.svc_safe_throttle import execute_safe_throttle
from think.services.strategy_select import  run_deterministic_math, extract_strategy_from_output
from think.helpers.update_state import update_battery_state_local_json as update_state

router = APIRouter(prefix="/dispatch", tags=["dispatch"])

import threading
import time

_dispatch_thread = None
_dispatch_running = False

def dispatch_loop():
    global _dispatch_running

    _dispatch_running = True

    while _dispatch_running:
        try:
            print("📡 Running data orchestrator")
            now = datetime.now()

            # 1. Pass time to the orchestrator to get fresh telemetry
            telemetry_data = build_llm_context(now)

            print("🧠 Running MCP agent")
            agent_raw_output = run_mcp_agent_flow(telemetry_data)
            strategy_intent = extract_strategy_from_output(agent_raw_output)

            # --- Indentation Fixed Here ---
            if not strategy_intent:
                print("⚠️ Agent failed to provide strategy JSON. Defaulting to SAFE_THROTTLE.")
                strategy_name = "SVC_SAFE_THROTTLE"
            else:
                strategy_name = strategy_intent.get("strategy", "SVC_SAFE_THROTTLE")

            # 2. Execute Deterministic Math Service
            dispatch_math = run_deterministic_math(strategy_name, telemetry_data)

            # 3. Update Persistence (Local JSON/DB)
            new_energy = dispatch_math['battery']['soc_after_mwh']
            capacity = telemetry_data['current_state']['battery']['capacity_mwh']
            
            # Logic for persistence
            update_state(new_energy, capacity)
            print(f"✅ State Updated: {new_energy} MWh")

            # 4. Final Response Assembly (Optional: store in history list)
            final_response = {
                "meta": {
                    "timestamp": telemetry_data['metadata']['trigger_timestamp'],
                    "region": telemetry_data['metadata']['region'],
                    "window_minutes": 30
                },
                "solar": dispatch_math['solar'],
                "battery": dispatch_math['battery'],
                "supply_mix": dispatch_math['supply_mix'],
                "carbon": dispatch_math['carbon'],
                "strategy_intent": strategy_intent,
                "reasoning": {
                    "why": agent_raw_output.split("Thought:")[-1].split("Action:")[0].strip() if "Thought:" in agent_raw_output else "Strategic optimization"
                },
                "summary": f"Executed {strategy_name}."
            }
            # Note: A background loop 'return' doesn't go to the user. 
            # You might want to append 'final_response' to a global history list here.

        except Exception as e:
            print(f"❌ Critical Failure: {str(e)}")
            # Fallback logic if needed, but usually we just log and wait for next cycle
        
        # --- Critical: Sleep must be inside the while loop ---
        print(f"😴 Cycle complete. Sleeping for 30 minutes...")
        time.sleep(30 * 60)

@router.post("/")
def dispatch():
    global _dispatch_thread, _dispatch_running

    if _dispatch_running:
        return {
            "status": "in_process",
            "interval_minutes": 30
        }

    _dispatch_thread = threading.Thread(
        target=dispatch_loop,
        daemon=True
    )
    _dispatch_thread.start()

    return {
        "status": "started",
        "interval_minutes": 30
    }

@router.get("/history")
def history(window: int = 30):
    """
    TEMP: call engine once and wrap as list
    until persistence layer exists.
    """

    fake_payload = {
        "solar_forecast": 11.2,
        "battery_soc": 24,
        "grid_intensity": 710,
        "load": 18,
    }

    decision = run_mcp_agent_flow(fake_payload)

    if isinstance(decision, str):
        import json
        try:
            decision = json.loads(decision)
        except:
            decision = {"raw": decision}

    return [decision]
