# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
import json
from typing import Dict, Any
from llmcontroller import run_mcp_agent_flow

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
        agent_result = run_mcp_agent_flow(telemetry_data)

        # 3. Handle Potential Parsing Issues
        # If the agent returned a string, try to parse it as JSON
        if isinstance(agent_result, str):
            try:
                final_json = json.loads(agent_result)
            except json.JSONDecodeError:
                # Fallback if the LLM added conversational text around the JSON
                final_json = {"raw_output": agent_result, "status": "check_parsing"}
        else:
            final_json = agent_result

        return final_json

    except Exception as e:
        print(f"❌ API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent Execution Failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)