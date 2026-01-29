# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import json
from typing import Dict, Any
from llmcontroller import run_mcp_agent_flow
from think.pydantic_classes import PhysicsSlice, CarbonSlice
from think.services.svc_safe_throttle import execute_safe_throttle
from think.services.strategy_select import extract_strategy_from_output, run_deterministic_math
from think.helpers.update_state import update_battery_state_local_json as update_state

app = FastAPI(title="Energy Decision Engine API")

# Define the input schema
class TelemetryRequest(BaseModel):
    metadata: Dict[str, Any]
    current_state: Dict[str, Any]
    grid_metrics: Dict[str, Any]
    forecast_context: Dict[str, Any]

@app.get("/")
def home():
    return {"status": "Decision Engine Online"}




@app.post("/process-decision")
async def process_decision(request: TelemetryRequest):
    try:
        # 1. Convert the Pydantic request model to a dictionary
        # This matches the 'telemetry_json' format your agent expects
        telemetry_data = request.dict()

        print(f"📡 Received telemetry for window: {telemetry_data.get('metadata', {}).get('trigger_timestamp')}")

        # 2. Call your Agent Flow
        # This triggers the Search -> Reason -> Tool Call (SVC) loop
        agent_raw_output = run_mcp_agent_flow(telemetry_data)
        strategy_intent = extract_strategy_from_output(agent_raw_output)

        if not strategy_intent:
            print("⚠️ Agent failed to provide strategy JSON. Defaulting to SAFE_THROTTLE.")
            strategy_name = "SVC_SAFE_THROTTLE"
        else:
            strategy_name = strategy_intent.get("strategy", "SVC_SAFE_THROTTLE")

        # 3. Execute Deterministic Math Service
        dispatch_math = run_deterministic_math(strategy_name, telemetry_data)

        # 4. Update Persistence Database
        # Save the new energy level for the next 30-minute call
        new_energy = dispatch_math['battery']['soc_after_mwh']
        new_soc = (new_energy /telemetry_data['current_state']['battery']['capacity_mwh']) * 100
        update_state(energy_mwh=new_energy, soc_percent=new_soc)

        # 5. Generate Final Rigid Output
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
            "strategy_intent": strategy_intent, # Keeps the AI's target_soc etc.
            "reasoning": {
                "why": agent_raw_output.split("Thought:")[-1].split("Action:")[0].strip()
            },
            "summary": f"Executed {strategy_name} to optimize renewable usage."
        }

        return final_response

    except Exception as e:
        print(f"❌ Critical Failure: {str(e)}")
        # If everything fails, return a safe throttle state without updating the DB
        return execute_safe_throttle(PhysicsSlice(**telemetry_data['current_state']))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)