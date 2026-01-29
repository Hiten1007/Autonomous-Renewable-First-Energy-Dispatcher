
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool  # Moved to core for stability
import langchainhub as hub


import langchainhub
from langchain_classic.agents import create_react_agent
from langchain_classic.agents import AgentExecutor

# --- AWS Specialized Package (The fix for your ImportError) ---
# This replaces the langchain_community version which was causing the error
from langchain_aws.retrievers import AmazonKnowledgeBasesRetriever

from think.pydantic_classes import PhysicsSlice, CarbonSlice, EnergyServiceInput, ToolInput
from think.services.svc_max_renewable import execute_max_renewable
from think.services.svc_peak_shaving import execute_peak_shaving
from think.services.svc_low_carbon_grid import execute_low_carbon_grid
from think.services.svc_safe_throttle import execute_safe_throttle
from think.brain.agent_prompts import AGENT_SYSTEM_PROMPT
from think.brain.llm import llm
import json
import traceback


# 1. Setup the Bedrock KB Retriever
# Use the Knowledge Base ID from your screenshot
RETRIEVER = AmazonKnowledgeBasesRetriever(
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
    agent_tools = [
        safety_tool, 
        max_renewable_tool, 
        peak_shaving_tool, 
        low_carbon_tool, 
        safe_throttle_tool
    ]

    # Use ONLY your system instructions as string - no template needed

    react_template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
{agent_scratchpad}"""
    
    prompt = PromptTemplate.from_template(react_template)
    
    # Add your system prompt at top
    full_prompt = PromptTemplate(
        template=f"{AGENT_SYSTEM_PROMPT}\n\n{react_template}",
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )
    
    agent = create_react_agent(llm, agent_tools, full_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True)
    
    
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