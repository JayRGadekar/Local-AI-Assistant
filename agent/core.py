from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import Tool
from agent.tools.file_search import search_files
from agent.tools.doc_reader import read_local_file

def initialize_agent():
    """
    Initialize the Agent with Ollama and tools using LangGraph.
    """
    llm = ChatOllama(model="llama3.2", temperature=0)

    # Define Tools
    # With @tool decorator, we can pass the functions directly
    tools = [search_files, read_local_file]

    # Construct Agent (LangGraph)
    # create_react_agent returns a CompiledGraph
    system_prompt = (
        "You are a helpful desktop assistant. Answer the user's questions in a short and concise manner, ideally within 3-4 sentences. "
        "If summarizing a document, keep it brief and focused on key points.\n"
        "IMPORTANT RULES:\n"
        "1. NEVER guess file paths. e.g. Do not assume '/Users/username/...'.\n"
        "2. ALWAYS use the 'search_files' tool to find the absolute path of a file before trying to read it.\n"
        "3. Only use 'read_local_file' once you have a confirmed path from the search tool.\n"
        "4. DO NOT output JSON schemas or tool definitions. JUST CALL THE TOOL.\n"
        "5. After searching, automatically pick the SINGLE BEST MATCHING file and read it immediately. Do not list other files or ask for clarification unless no good match is found."
    )
    agent_executor = create_react_agent(model=llm, tools=tools, prompt=system_prompt)

    return agent_executor
