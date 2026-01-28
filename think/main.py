# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
app = FastAPI(title="Energy Decision Engine API")

# Define the input schema
class ForecastRequest(BaseModel):
    trigger_time: str  # Format: "YYYY-MM-DD HH:mm:ss"
    horizon: int = 6

@app.get("/")
def home():
    return {"status": "Decision Engine Online"}

@app.post("/process-decision")
async def process_decision(request: ForecastRequest):
    try:
      return 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)