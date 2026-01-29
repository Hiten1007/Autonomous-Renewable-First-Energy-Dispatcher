from langchain_community.chat_models import ChatOllama

print("Initializing the LLM instance...")
llm = ChatOllama(model="granite3-dense", temperature=0)
print("LLM instance created.")