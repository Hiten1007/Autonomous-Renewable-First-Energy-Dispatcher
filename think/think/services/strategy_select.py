import re
import json
from think.pydantic_classes import PhysicsSlice, CarbonSlice
from .svc_max_renewable import execute_max_renewable
from .svc_peak_shaving import execute_peak_shaving
from .svc_low_carbon_grid import execute_low_carbon_grid
from .svc_safe_throttle import execute_safe_throttle
# --- STRATEGY TO SERVICE MAPPING ---
STRATEGY_MAP = {
    "SVC_MAX_RENEWABLE": execute_max_renewable,
    "SVC_PEAK_SHAVING": execute_peak_shaving,
    "SVC_LOW_CARBON_GRID": execute_low_carbon_grid,
    "SVC_SAFE_THROTTLE": execute_safe_throttle
}

def extract_strategy_from_output(agent_output: str):
    """
    Cleans and extracts the Strategy JSON from the LLM text.
    """
    try:
        # Look for the JSON block inside the agent's final answer
        match = re.search(r"(\{.*strategy.*\})", agent_output, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return None
    except Exception:
        return None

def run_deterministic_math(strategy_name: str, telemetry: dict):
    service_func = STRATEGY_MAP.get(strategy_name, execute_safe_throttle)
    
    state = telemetry['current_state']
    batt = state['battery']
    
    if strategy_name in ["SVC_PEAK_SHAVING", "SVC_LOW_CARBON_GRID"]:
        data = CarbonSlice(
            solar=state['actual_solar_mwh'], 
            load=state['actual_load_mwh'], 
            battery_energy=batt['energy_mwh'], 
            battery_capacity=batt['capacity_mwh'], 
            soc=batt['soc_percent'],
            grid_intensity=telemetry['grid_metrics']['carbon_intensity_direct_gco2_per_kwh']
        )
    else:
        data = PhysicsSlice(
            solar=state['actual_solar_mwh'], 
            load=state['actual_load_mwh'], 
            battery_energy=batt['energy_mwh'], 
            battery_capacity=batt['capacity_mwh'], 
            soc=batt['soc_percent']
        )
        
    return service_func(data)

