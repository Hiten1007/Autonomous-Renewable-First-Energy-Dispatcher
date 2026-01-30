# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import json
from typing import Dict, Any
from llmcontroller import run_mcp_agent_flow
from think.pydantic_classes import PhysicsSlice, CarbonSlice
from think.services.svc_safe_throttle import execute_safe_throttle
from think.services.strategy_select import  run_deterministic_math, extract_strategy_from_output
from think.helpers.update_state import update_battery_state_local_json as update_state
from think.dispatch import router as dispatch_router

app = FastAPI(title="Energy Decision Engine API")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # 1. Import the middleware

app = FastAPI()

# 2. Define the allowed origins
origins = [
    "http://localhost:5173",  # Your React Frontend
    "http://127.0.0.1:5173",
]

# 3. Add the middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

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
    # Use model_dump() instead of dict() for Pydantic V2
    telemetry_data = request.model_dump()
    
    try:
        print(f"📡 Received telemetry for window: {telemetry_data.get('metadata', {}).get('trigger_timestamp')}")

        # 1. Call Agent Flow (Strategy Selection)
        agent_raw_output = run_mcp_agent_flow(telemetry_data)
        strategy_intent = extract_strategy_from_output(agent_raw_output)

        if not strategy_intent:
            print("⚠️ Agent failed to provide strategy JSON. Defaulting to SAFE_THROTTLE.")
            strategy_name = "SVC_SAFE_THROTTLE"
        else:
            strategy_name = strategy_intent.get("strategy", "SVC_SAFE_THROTTLE")

        # 2. Execute Deterministic Math Service
        dispatch_math = run_deterministic_math(strategy_name, telemetry_data)

        # 3. Update Persistence (Local JSON/DB)
        new_energy = dispatch_math['battery']['soc_after_mwh']
        # Use the capacity from the input data
        capacity = telemetry_data['current_state']['battery']['capacity_mwh']
        new_soc = (new_energy / capacity) * 100
        update_state(new_energy, capacity)

        # 4. Final Response Assembly
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
        return final_response

    except Exception as e:
        print(f"❌ Critical Failure: {str(e)}")
        # Mapping for the Fallback
        state = telemetry_data['current_state']
        fallback_slice = PhysicsSlice(
            solar=state['actual_solar_mwh'],
            load=state['actual_load_mwh'],
            battery_energy=state['battery']['energy_mwh'],
            battery_capacity=state['battery']['capacity_mwh'],
            soc=state['battery']['soc_percent']
        )
        return execute_safe_throttle(fallback_slice)
    
app.include_router(dispatch_router)
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)