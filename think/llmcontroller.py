
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
    Queries the AWS Bedrock Knowledge Base for energy safety protocols.
    """
    # Use invoke() for AmazonKnowledgeBasesRetriever
    docs = RETRIEVER.invoke(query)
    
    if not docs:
        return "No specific safety protocols found for this query. Default to SAFE_MODE."
    
    # Combine retrieved snippets
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
    # Use ONLY your system instructions as string - no template needed
 

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