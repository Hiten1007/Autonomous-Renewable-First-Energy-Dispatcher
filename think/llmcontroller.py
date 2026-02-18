
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import StructuredTool

from langchain_classic.agents import create_react_agent
from langchain_classic.agents import AgentExecutor

# --- LOCAL VECTOR STORE (replaces AWS Bedrock) ---
from think.knowledge_base.local_vector_store import query_knowledge_base

from think.pydantic_classes import PhysicsSlice, CarbonSlice, EnergyServiceInput, ToolInput

from think.brain.agent_prompts import AGENT_SYSTEM_PROMPT
from think.brain.llm import llm
import json
import traceback


def safety_protocol_search_wrapper(query: str):
    """
    Queries the LOCAL ChromaDB Knowledge Base for energy safety protocols.
    Drop-in replacement for the old AWS Bedrock retriever.
    """
    result = query_knowledge_base(query, n_results=3)
    
    if not result or result.strip() == "":
        return "No specific safety protocols found for this query. Default to SAFE_MODE."
    
    return result


# Define the Tool for the Agent (same interface as before)
safety_tool = StructuredTool.from_function(
    func=safety_protocol_search_wrapper,
    name="Safety_Protocol_Search",
    description="Search Knowledge Base for safety limits, carbon thresholds, battery protocols. Example: 'Haryana carbon intensity limits'",
    args_schema=ToolInput
)

def get_mcp_agent():
    agent_tools = [
        safety_tool, 
    ]

    full_template = f"""{AGENT_SYSTEM_PROMPT}

{{tools}}

Use this format:
Question: {{input}}
Thought: {{agent_scratchpad}}"""
    
    prompt = PromptTemplate.from_template(full_template)
    
    agent = create_react_agent(llm, agent_tools, prompt)
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

        agent_response = mcp_agent_executor.invoke({
            "input": "Analyze the provided telemetry and execute the optimal SVC strategy service.",
            "telemetry_data": telemetry_string,
            "chat_history": chat_history,
        })
        
        final_output = agent_response.get('output', '')
        
        return final_output
        
    except Exception as e:
        print(f"FATAL ERROR: {traceback.format_exc()}")
        return {"status": "error", "message": str(e)}