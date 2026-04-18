from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Literal
from datetime import datetime

class BatteryInput(BaseModel):
    energy_mwh: float = Field(..., ge=0)
    capacity_mwh: float = Field(..., gt=0)
    soc_percent: float = Field(..., ge=0, le=100)

class CurrentState(BaseModel):
    resolution: str
    actual_solar_mwh: float = Field(..., ge=0)
    actual_load_mwh: float = Field(..., ge=0)
    battery: BatteryInput

class GridMetrics(BaseModel):
    carbon_intensity_direct_gco2_per_kwh: int
    renewable_percentage: float

class ForecastItem(BaseModel):
    t_plus_hours: int
    forecast_solar_mwh: float
    forecast_load_mwh: float
    net_demand_mwh: float

class TelemetryInput(BaseModel):
    metadata: Dict[str, str]
    current_state: CurrentState
    grid_metrics: GridMetrics
    forecast_context: Dict[str, List[ForecastItem]]

from pydantic import BaseModel

# What every service needs: Current Energy Balance
class PhysicsSlice(BaseModel):
    solar: float
    load: float
    battery_energy: float
    battery_capacity: float
    soc: float

# Extra data for Carbon-based services
class CarbonSlice(PhysicsSlice):
    grid_intensity: float

# --- AGENT PERSISTENCE SCHEMA ---
class EnergyServiceInput(BaseModel):
    telemetry: dict = Field(..., description="The full telemetry JSON object provided in the context.")

class ToolInput(BaseModel):
    """
    Schema for the Knowledge Base search tool.
    This tells the Agent to provide a specific string for the vector search.
    """
    query: str = Field(
        ..., 
        description="The semantic search query used to find safety protocols (e.g., 'battery SOC limits' or 'Haryana carbon thresholds')."
    )
class UnifiedTelemetry(BaseModel):
    """Complete data center telemetry for the multi-agent system."""
    metadata: Dict[str, str]
    current_state: CurrentState
    it_metrics: ITMetrics
    thermal_metrics: ThermalMetrics
    cooling_metrics: CoolingMetrics
    grid_metrics: Dict[str, float]
    forecast_context: Dict