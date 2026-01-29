from langchain.prompts import PromptTemplate
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor
from pydantic_classes import PhysicsSlice, CarbonSlice, EnergyServiceInput, ToolInput
from think.services.svc_max_renewable import execute_max_renewable
from think.services.svc_peak_shaving import execute_peak_shaving
from think.services.svc_low_carbon_grid import execute_low_carbon_grid
from think.services.svc_safe_throttle import execute_safe_throttle
from think.brain.agent_prompts import AGENT_SYSTEM_PROMPT
from langchain.tools import StructuredTool
from think.brain.llm import llm
import json
import traceback


import boto3
from langchain_community.retrievers import AmazonBedrockKnowledgeBaseRetriever
from langchain.tools import StructuredTool

# 1. Setup the Bedrock KB Retriever
# Use the Knowledge Base ID from your screenshot
RETRIEVER = AmazonBedrockKnowledgeBaseRetriever(
    knowledge_base_id="YX0BXMRB7Z",
    retrieval_config={
        "vectorSearchConfiguration": {
            "numberOfResults": 3  # Top 3 most relevant safety protocols
        }
    }
)

def safety_protocol_search_wrapper(query: str):
    """
    Queries the AWS Bedrock Knowledge Base for energy safety 
    protocols and regional constraints.
    """
    # This hits your S3-backed OpenSearch index
    docs = RETRIEVER.get_relevant_documents(query)
    
    if not docs:
        return "No specific safety protocols found for this query. Default to SAFE_MODE."
    
    # Combine the retrieved technical snippets
    return "\n\n".join([doc.page_content for doc in docs])

# 2. Define the Tool for the Agent
safety_tool = StructuredTool.from_function(
    func=safety_protocol_search_wrapper, 
    name="Safety_Protocol_Search",
    description="""
        Use this tool to retrieve regional safety limits, carbon thresholds, 
        and battery protocols from the technical manual. 
        Input should be a specific search query like 'Haryana carbon intensity limits'.
    """,
    args_schema=ToolInput # Your single-string input schema
)


# Assuming the Pydantic slices and math functions from the previous step are imported
def max_renewable_wrapper(telemetry: dict):
    # Prune data to PhysicsSlice
    data = PhysicsSlice(**telemetry['current_state'], **telemetry['current_state']['battery'])
    return execute_max_renewable(data)

def peak_shaving_wrapper(telemetry: dict):
    # Prune data to CarbonSlice
    data = CarbonSlice(**telemetry['current_state'], **telemetry['current_state']['battery'], 
                       grid_intensity=telemetry['grid_metrics']['carbon_intensity_direct_gco2_per_kwh'])
    return execute_peak_shaving(data)

def low_carbon_wrapper(telemetry: dict):
    data = CarbonSlice(**telemetry['current_state'], **telemetry['current_state']['battery'], 
                       grid_intensity=telemetry['grid_metrics']['carbon_intensity_direct_gco2_per_kwh'])
    return execute_low_carbon_grid(data)

def safe_throttle_wrapper(telemetry: dict):
    data = PhysicsSlice(**telemetry['current_state'], **telemetry['current_state']['battery'])
    return execute_safe_throttle(data)

# --- 1. MAX RENEWABLE TOOL ---
max_renewable_tool = StructuredTool.from_function(
    func=max_renewable_wrapper,
    name="SVC_MAX_RENEWABLE",
    description="""
        Use this tool when solar surplus is detected (net_demand is negative). 
        This tool prioritizes solar usage for load and battery charging before exporting.
        OUTPUT: Rigid JSON for 'Renewable-First' dispatch.
    """,
    args_schema=EnergyServiceInput
)

# --- 2. PEAK SHAVING TOOL ---
peak_shaving_tool = StructuredTool.from_function(
    func=peak_shaving_wrapper,
    name="SVC_PEAK_SHAVING",
    description="""
        Use this tool during high load or when grid carbon intensity is high (>600).
        This tool calculates battery discharge to shave the peak demand.
        OUTPUT: Rigid JSON for battery-assisted load coverage.
    """,
    args_schema=EnergyServiceInput
)

# --- 3. LOW CARBON GRID TOOL ---
low_carbon_tool = StructuredTool.from_function(
    func=low_carbon_wrapper,
    name="SVC_LOW_CARBON_GRID",
    description="""
        Use this tool when local generation is zero but the grid is currently clean/cheap.
        This tool calculates grid-to-battery charging to prepare for future peaks.
        OUTPUT: Rigid JSON for strategic grid import.
    """,
    args_schema=EnergyServiceInput
)

# --- 4. SAFE THROTTLE TOOL ---
safe_throttle_tool = StructuredTool.from_function(
    func=safe_throttle_wrapper,
    name="SVC_SAFE_THROTTLE",
    description="""
        The mandatory fallback tool. Use if telemetry is missing, contradictory, 
        or if the Knowledge Base indicates a safety protocol violation.
        OUTPUT: Rigid JSON for system protection (Battery IDLE).
    """,
    args_schema=EnergyServiceInput
)

# --- 5. THE KNOWLEDGE BASE TOOL (RAG) ---
# (Added for the MCP Reasoning loop)
safety_tool = StructuredTool.from_function(
    func=safety_protocol_search_wrapper, 
    name="Safety_Protocol_Search",
    description="""
        Search the Knowledge Base for safety limits, regional thresholds, and carbon protocols.
        Call this BEFORE choosing an SVC tool to validate thresholds.
    """,
    args_schema=ToolInput # Single string query schema
)

def get_mcp_agent():
    """Initializes the agent with Pinned Telemetry Persistence."""
    
    # 1. Your defined tools (SVCs and RAG)
    tools = [safety_tool, max_renewable_tool, peak_shaving_tool, low_carbon_tool, safe_throttle_tool]

    # 2. Pull the base ReAct prompt
    base_prompt = hub.pull("hwchase17/react-chat")

    # 3. Create a Custom Template that pins the Telemetry at the top
    # This ensures the LLM sees the data BEFORE it starts its "Thought" loop
    persistent_template = f"""
{AGENT_SYSTEM_PROMPT}

--- GLOBAL CURRENT TELEMETRY ---
{{telemetry_data}}
--- END GLOBAL CONTEXT ---

{base_prompt.template}
"""
    
    prompt = PromptTemplate.from_template(template=persistent_template)

    # 4. Create the Agent
    agent = create_react_agent(llm, tools, prompt)

    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        # IMPORTANT: Max iterations ensures it doesn't loop infinitely 
        # but has enough "memory" to finish the task
        max_iterations=5 
    )
    return agent_executor

mcp_agent_executor = get_mcp_agent()

def run_mcp_agent_flow(telemetry_json: dict, chat_history: list = None):
    """
    Executes the agent while ensuring the telemetry data persists in the context window.
    """
    try:
        if chat_history is None:
            chat_history = []

        # Convert the dict to a formatted string for the prompt
        telemetry_string = json.dumps(telemetry_json, indent=2)

        # We pass the telemetry into the 'telemetry_data' slot we created in the prompt
        # and a simple trigger into the 'input' slot.
        agent_response = mcp_agent_executor.invoke({
            "input": "Analyze the provided telemetry and execute the optimal SVC strategy service.",
            "telemetry_data": telemetry_string,
            "chat_history": chat_history,
        })
        
        final_output = agent_response.get('output', '')
        
        # Persistence check: If the output doesn't look like our Rigid JSON, 
        # we know it lost context (though pinning usually prevents this)
        return final_output
        
    except Exception as e:
        print(f"FATAL ERROR: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}