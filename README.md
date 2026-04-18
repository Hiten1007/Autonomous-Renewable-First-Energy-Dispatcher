# ⚡ Autonomous Renewable First Energy Dispatcher (ARFED)

> **An AI-native, agentic energy management system that autonomously optimizes solar dispatch, battery storage, and grid interaction for the Haryana/NCR region of Northern India — in real time.**

---

## 📌 Table of Contents

- [Overview](#overview)
- [Project Architecture](#project-architecture)
- [System Design](#system-design)
  - [Sense Layer](#1-sense-layer)
  - [Think Layer (AI Brain)](#2-think-layer-ai-brain)
  - [Act Layer (Dispatch Strategies)](#3-act-layer-dispatch-strategies)
  - [Display Layer (Dashboard)](#4-display-layer-dashboard)
- [Dispatch Strategies](#dispatch-strategies)
- [API Reference](#api-reference)
- [Directory Structure](#directory-structure)
- [Data Sources](#data-sources)
- [Setup & Installation](#setup--installation)
- [Running the System](#running-the-system)
- [Environment Variables](#environment-variables)
- [Key Design Decisions](#key-design-decisions)

---

## Overview

ARFED is a full-stack, autonomous energy dispatch system built for the **HackVeda** hackathon. It embodies the **Renewable-First** philosophy: every watt of solar energy must be consumed or stored before importing from the grid.

The system operates on a **30-minute control cycle** and makes fully autonomous decisions by:

1. **Sensing** real-time solar output, grid load, battery state, and carbon intensity
2. **Thinking** using a LangChain ReAct Agent (the *H-Energy Strategic Cortex*) powered by a local LLM
3. **Acting** by executing one of 4 physics-based dispatch strategies
4. **Displaying** results on a live React dashboard

This is not a simulation — it pulls **live weather data**, **live grid carbon metrics** (via Electricity Maps API), and uses **trained ML models** for solar and load forecasting.

---

## Project Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        ARFED System                                │
│                                                                    │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────────────┐   │
│  │  SENSE   │───▶│    THINK     │───▶│         ACT            │   │
│  │          │    │ (AI Agent)   │    │  (Dispatch Strategies) │   │
│  │ • Solar  │    │              │    │                        │   │
│  │   forecast    │ • ReAct Agent│    │ • SVC_MAX_RENEWABLE    │   │
│  │ • Load   │    │ • LangChain  │    │ • SVC_PEAK_SHAVING     │   │
│  │   forecast    │ • FAISS KB   │    │ • SVC_LOW_CARBON_GRID  │   │
│  │ • Grid   │    │ • Strategy   │    │ • SVC_SAFE_THROTTLE    │   │
│  │   carbon │    │   selection  │    │                        │   │
│  │ • Battery│    └──────────────┘    └────────────────────────┘   │
│  │   state  │                                    │                 │
│  └──────────┘                                    ▼                 │
│                                       ┌──────────────────┐        │
│                                       │   FASTAPI SERVER │        │
│                                       │  (Decision Engine│        │
│                                       │    + Dispatcher) │        │
│                                       └──────────────────┘        │
│                                                │                   │
│                                                ▼                   │
│                                       ┌──────────────────┐        │
│                                       │  React Dashboard  │        │
│                                       │  (Vite + Charts) │        │
│                                       └──────────────────┘        │
└────────────────────────────────────────────────────────────────────┘
```

---

## System Design

### 1. Sense Layer

**Location:** `think/think/sense/`

The Sense layer is the system's perception module. It aggregates data from multiple real-world sources into a unified telemetry context every 30 minutes.

| Module | Purpose | Source |
|---|---|---|
| `live_predictor.py` | Solar energy forecast (6-hour horizon) | VisualCrossing Weather API + trained ML model |
| `load_predictor.py` | Electricity load forecast (6-hour horizon) | Haryana historical generation data + ML model |
| `grid_carbon_info.py` | Live carbon intensity & renewable % | Electricity Maps API (`IN-NO` zone) |
| `get_battery_state.py` | Current battery SOC and energy | Local `battery_state.json` |
| `real_values.py` | Actual 30-min solar & load readings | Simulated/real data source |
| `data_orchestrator.py` | **Assembles all of the above** into one JSON payload | — |

#### Solar Forecasting Model

The solar forecast model is a **multi-output regressor** trained on NASA POWER satellite data for 5 Haryana cities (Panchkula, Rohtak, Gurugram, Hisar, Yamunanagar). Key features include:

- Cyclic time encoding (`hour_sin`, `hour_cos`, `month_sin`, `month_cos`)
- Clear-sky index (`ALLSKY_KT_HOURLY`) derived from live cloud cover
- Lag features: 1h, 3h, 6h, 24h solar lags + rolling means
- **Hard Night Gating**: predictions are forced to 0 between 19:00 and 06:00

#### Telemetry Payload Structure

```json
{
  "metadata": { "trigger_timestamp": "ISO datetime", "region": "IN-NO" },
  "current_state": {
    "resolution": "30min",
    "actual_solar_mwh": 1500.0,
    "actual_load_mwh": 2000.0,
    "battery": { "energy_mwh": 3000, "capacity_mwh": 5200, "soc_percent": 57.7 }
  },
  "grid_metrics": {
    "carbon_intensity_direct_gco2_per_kwh": 450,
    "carbon_intensity_lifecycle_gco2_per_kwh": 520,
    "renewable_percentage": 22.5,
    "carbon_free_percentage": 24.0
  },
  "forecast_context": {
    "resolution": "hourly",
    "horizon_hours": 6,
    "data": [
      { "t_plus_hours": 1, "forecast_solar_mwh": 1200, "forecast_load_mwh": 2500, "net_demand_mwh": 1300 }
    ]
  }
}
```

---

### 2. Think Layer (AI Brain)

**Location:** `think/think/brain/` and `think/llmcontroller.py`

The Think layer is the system's intelligence. It uses a **LangChain ReAct Agent** — the *H-Energy Strategic Cortex* — to reason over telemetry and select the optimal dispatch strategy.

#### Agent Architecture

```
LangChain ReAct Agent
├── System Prompt: AGENT_SYSTEM_PROMPT (agent_prompts.py)
│   ├── Regional context: Haryana rules (7 PM Rule, winter fog, Sunday bias)
│   ├── Core rules: RENEWABLE-FIRST, CARBON-AWARENESS, SAFETY-ABOVE-ALL
│   ├── 5-step decision algorithm
│   └── Output format specification
├── Tool: Safety_Protocol_Search
│   └── Queries local FAISS vector store (schemas/index.faiss)
│       for safety limits, carbon thresholds, battery protocols
└── LLM: Configurable (brain/llm.py)
```

#### FAISS Knowledge Base

The agent's safety tool queries a local FAISS vector index (`schemas/index.faiss`) that stores energy safety protocols. This replaces a cloud-based retrieval system and runs entirely offline. It was built using `schemas/create_vector_store.py`.

#### Agent Decision Algorithm (5 Steps)

| Step | Description |
|---|---|
| **1. Safety Check** | If SOC < 15% or telemetry missing → `SVC_SAFE_THROTTLE` immediately |
| **2. Analyze Current State** | Read solar, load, battery SOC, carbon intensity |
| **3. Analyze Forecast** | Count negative `net_demand_mwh` hours; check load ramp |
| **4. Retrieve Safety Limits** | Call `Safety_Protocol_Search` tool |
| **5. Select Strategy** | Apply priority: Safe > Max Renewable > Peak Shaving > Low Carbon > Safe |

#### Regional Intelligence (Haryana-Specific Rules)

The agent is tuned with hard-coded knowledge about the Haryana/NCR grid:

- **7 PM Rule**: If SOC > 50% at 19:00+, force `SVC_PEAK_SHAVING` (coal-heavy evening grid)
- **Winter Fog Awareness**: If forecast solar is high but actual ≈ 0, distrust the forecast
- **Sunday Bias**: Industrial load drops ~20%; bias toward `SVC_MAX_RENEWABLE`
- **Carbon Threshold**: Evening coal intensity often exceeds 750 gCO2/kWh

---

### 3. Act Layer (Dispatch Strategies)

**Location:** `think/think/services/`

Once the agent selects a strategy name (`SVC_*`), the `strategy_select.py` router calls the corresponding deterministic math service. All services are pure functions operating on typed Pydantic slices.

#### Data Models (`pydantic_classes.py`)

```python
PhysicsSlice   # solar, load, battery_energy, battery_capacity, soc
CarbonSlice    # extends PhysicsSlice with grid_intensity
```

---

## Dispatch Strategies

### `SVC_MAX_RENEWABLE`

**When**: Solar surplus (net demand is negative for >50% of the 6-hour forecast window)

**Logic**:
```
used_directly = min(solar, load)
surplus_solar = solar - load
stored        = min(surplus_solar, battery_headroom, 2.0 MWh cap)
curtailed     = surplus_solar - stored
grid_import   = max(0, load - used_directly)
```
Battery mode: **CHARGE (SOLAR_ONLY)**

---

### `SVC_PEAK_SHAVING`

**When**: Forecast load ramps >25% over 3 hours AND SOC > 40%, OR Hour ≥ 19:00 AND SOC > 50%

**Logic**:
```
load_gap    = load - solar
usable      = battery_energy - (20% SOC floor × capacity)
discharged  = min(load_gap, usable, 2.5 MWh cap)
grid_import = max(0, load_gap - discharged)
```
Battery mode: **DISCHARGE** (stops at 20% SOC floor)

---

### `SVC_LOW_CARBON_GRID`

**When**: Night time (solar ≈ 0) AND carbon intensity < 500 gCO2/kWh AND SOC < 60%

**Logic**:
```
target_soc     = 70% (leave headroom for morning solar)
charge_needed  = (target_soc - current_soc) × capacity
charge_amount  = min(charge_needed, 2.0 MWh cap)
```
Battery mode: **CHARGE (GRID_ALLOWED)** — pre-charges during clean grid windows

---

### `SVC_SAFE_THROTTLE`

**When**: SOC < 15%, missing/contradictory telemetry, or fallback for any agent failure

**Logic**: Battery IDLE — no charge, no discharge. Serves load from solar + grid only.

This is also the **guaranteed fallback** path. If the LLM agent crashes or returns invalid output, the API's `except` block automatically calls `execute_safe_throttle`.

---

## API Reference

**Backend**: FastAPI server running on `http://localhost:8000`

### `GET /`
Health check.
```json
{ "status": "Decision Engine Online" }
```

### `POST /process-decision`
Submit a one-shot telemetry payload for immediate strategy evaluation.

**Request body**: Full telemetry JSON (see [Telemetry Payload Structure](#telemetry-payload-structure))

**Response**:
```json
{
  "meta": { "timestamp": "...", "region": "IN-NO", "window_minutes": 30 },
  "solar": { "generated_mwh": ..., "used_directly_mwh": ..., "stored_mwh": ..., "curtailed_mwh": ... },
  "battery": { "state": "CHARGE", "soc_before_mwh": ..., "soc_after_mwh": ..., "delta_mwh": ... },
  "supply_mix": { "local_renewables_mwh": ..., "grid_import_mwh": ..., "effective_re_percent": ... },
  "carbon": { "grid_intensity_gco2_per_kwh": ..., "saved_kgco2": ..., "actual_kgco2": ..., "baseline_kgco2": ... },
  "strategy_intent": { "strategy": "SVC_MAX_RENEWABLE", "battery_intent": {...}, "reasoning": {...} },
  "reasoning": { "why": "..." },
  "summary": "Executed SVC_MAX_RENEWABLE."
}
```

### `POST /dispatch/`
Triggers the autonomous 30-minute dispatch loop (runs in a background daemon thread). Also returns current dispatch history from `dispatch_data.json`.

### `GET /dispatch/history`
Returns the last 100 dispatch records as a JSON array.

---

## Directory Structure

```
Autonomous Renewable First Energy Dispatcher/
│
├── think/                          # Backend (FastAPI)
│   ├── main.py                     # FastAPI app + /process-decision endpoint
│   ├── llmcontroller.py            # LangChain ReAct agent setup + runner
│   ├── battery_state.json          # Persisted battery SOC state
│   ├── dispatch_data.json          # Rolling 100-entry dispatch history
│   └── think/                      # Core Python package
│       ├── pydantic_classes.py     # All Pydantic data models
│       ├── dispatch.py             # /dispatch/ router + 30-min loop
│       ├── brain/
│       │   ├── agent_prompts.py    # H-Energy Strategic Cortex system prompt
│       │   └── llm.py              # LLM client configuration
│       ├── sense/
│       │   ├── data_orchestrator.py    # Assembles full telemetry context
│       │   ├── live_predictor.py       # Solar forecast (ML model + weather API)
│       │   ├── load_predictor.py       # Load forecast (ML model)
│       │   ├── grid_carbon_info.py     # Electricity Maps API connector
│       │   ├── get_battery_state.py    # Reads battery_state.json
│       │   ├── real_values.py          # Actual 30-min readings
│       │   ├── solar_forecast_model.pkl    # Trained solar regression model (~17MB)
│       │   ├── fixed_load_meter_model.pkl  # Trained load regression model (~16MB)
│       │   └── scaler.pkl              # Feature scaler for solar model
│       ├── services/
│       │   ├── strategy_select.py      # Strategy router + JSON extractor
│       │   ├── svc_max_renewable.py    # Maximize solar storage
│       │   ├── svc_peak_shaving.py     # Discharge battery at peak demand
│       │   ├── svc_low_carbon_grid.py  # Pre-charge on clean grid
│       │   └── svc_safe_throttle.py    # Safe fallback (battery idle)
│       ├── helpers/
│       │   ├── update_state.py         # Persists new battery SOC
│       │   └── calculate_carbon_impact.py
│       └── knowledge_base/
│           └── local_vector_store.py   # FAISS query interface
│
├── schemas/
│   ├── create_vector_store.py      # Script to build FAISS index from protocols
│   ├── index.faiss                 # FAISS vector index (safety protocols)
│   └── index_to_doc.pkl            # FAISS document map
│
├── dashboard/
│   └── carbon-dispatch-dashboard/  # React + Vite frontend
│       ├── src/
│       │   ├── components/         # UI components (charts, panels)
│       │   ├── hooks/              # Data fetching hooks
│       │   ├── layout/             # Page layout components
│       │   └── styles/             # CSS modules
│       └── package.json
│
├── data/
│   ├── FINAL_ALL_FEATURES.csv              # Master training dataset
│   ├── compile_data.py                     # Data compilation script
│   ├── preprocess_data.ipynb               # EDA + preprocessing notebook
│   └── [solar_energy/, WIND SPEED/, TEMP/, CI/, load_meter/]  # Raw data by feature
│
├── lambda_layer/                   # Offline FAISS/NumPy dependencies (for AWS Lambda portability)
├── example.json                    # Example telemetry payload for API testing
├── battery_state.json              # Root-level battery state (top-level reference)
└── pitch_deck.html                 # Project pitch deck (standalone HTML)
```

---

## Data Sources

| Source | Description | Used For |
|---|---|---|
| **NASA POWER API** | Satellite-based solar irradiance, temperature, wind | Training solar forecast model |
| **Haryana SLDC** | Historical state-level generation data | Training load forecast model |
| **VisualCrossing Weather API** | Live hourly weather for 5 Haryana cities | Real-time feature engineering for solar forecast |
| **Electricity Maps API** | Live carbon intensity (direct & lifecycle) + renewable % for `IN-NO` zone | Grid carbon metrics in telemetry |
| **Local `battery_state.json`** | Persisted battery energy (MWh) and capacity | Battery SOC continuity between cycles |

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Node.js 18+ (for the dashboard)
- pip

### Backend Setup

```bash
# Navigate to the backend directory
cd "Autonomous Renewable First Energy Dispatcher/think"

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate # Linux/Mac

# Install dependencies
pip install fastapi uvicorn langchain langchain-core langchain-classic \
            pydantic python-dotenv requests numpy pandas joblib faiss-cpu

# (Optional) Rebuild the FAISS knowledge base if needed
cd ..
python schemas/create_vector_store.py
```

### Dashboard Setup

```bash
cd "dashboard/carbon-dispatch-dashboard"
npm install
```

---

## Running the System

### Step 1: Start the Backend API

```bash
cd "Autonomous Renewable First Energy Dispatcher/think"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Visit `/docs` for the interactive Swagger UI.

### Step 2: Start the Dashboard

```bash
cd "dashboard/carbon-dispatch-dashboard"
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### Step 3: Trigger the Dispatch Loop

Send a `POST` request to `/dispatch/` (using the dashboard or curl) to start the autonomous 30-minute dispatch loop:

```bash
curl -X POST http://localhost:8000/dispatch/
```

### Step 4: Test with a Manual Payload

Use the provided `example.json` to test `/process-decision`:

```bash
curl -X POST http://localhost:8000/process-decision \
     -H "Content-Type: application/json" \
     -d @example.json
```

---

## Environment Variables

Create a `.env` file inside the `think/` directory:

```env
# Electricity Maps API (for live carbon intensity)
ELECTRICITY_MAPS_API_KEY=your_electricity_maps_key_here

# LLM Provider (configure in think/think/brain/llm.py)
# Supports any LangChain-compatible LLM (OpenAI, Google Gemini, local Ollama, etc.)
OPENAI_API_KEY=your_openai_key_here
```

> **Note:** The VisualCrossing Weather API key is currently hardcoded in `live_predictor.py`. Move it to `.env` for production use.

---

## Key Design Decisions

### 1. Deterministic Math After LLM Strategy Selection
The LLM agent is only responsible for **selecting a strategy name** (e.g., `"SVC_PEAK_SHAVING"`). All actual energy math is done by pure Python functions — this eliminates hallucinated numbers and ensures physical correctness.

### 2. Local FAISS Knowledge Base Instead of Cloud RAG
Safety protocols are stored in a local FAISS vector index rather than a cloud-based retrieval system (e.g., AWS Bedrock). This makes the system run fully offline and avoids API costs for knowledge retrieval.

### 3. Hard Fallback Safety Net
Every code path that can fail (LLM timeout, bad JSON, API error) falls back to `SVC_SAFE_THROTTLE`. The battery never violates its 15% floor or 98% ceiling regardless of agent output.

### 4. JSON-Persisted Battery State
Battery SOC is persisted to `battery_state.json` after every dispatch cycle. This ensures continuity across API restarts without requiring a database.

### 5. Renewable-First Philosophy
The priority order of strategies is architecturally enforced: solar storage is always preferred over grid interaction, and grid import is always the last resort.

---

## Acknowledgements

Built for the **HackVeda** hackathon. Data sourced from NASA POWER, Haryana SLDC, VisualCrossing, and Electricity Maps. Renewable-first dispatch logic inspired by India's National Electricity Plan (2023) targets for 500 GW non-fossil capacity by 2030.
