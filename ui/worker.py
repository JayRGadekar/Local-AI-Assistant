from PyQt6.QtCore import QThread, pyqtSignal
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
import uuid
import re
import json

class AgentWorker(QThread):
    """
    Async worker to run the LangChain agent without freezing the UI.
    """
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, agent_executor, chat_history: list):
        super().__init__()
        self.agent_executor = agent_executor
        self.chat_history = chat_history

    def run(self):
        try:
            # Invoke the agent with the full history
            print(f"DEBUG WORKER: Invoking agent with history: {self.chat_history}")
            response = self.agent_executor.invoke({"messages": self.chat_history})
            print(f"DEBUG WORKER: Full Agent Response: {response}")
            
            last_message = response['messages'][-1]
            output = last_message.content

            # FALLBACK: If model outputs a raw JSON tool call OR just says "Reading local file: ..."
            json_match = None
            text_command_match = None
            
            if not last_message.tool_calls:
                 # Check for JSON first
                 match = re.search(r'(\{[\s\r\n]*"name"[\s\r\n]*:[\s\r\n]*".*?\})', output, re.DOTALL)
                 if match:
                      json_candidate = output[match.start():]
                      json_match = json_candidate
                 
                 # Check for Text Pattern: "Reading local file: <path>"
                 # This is common when the model is lazy.
                 else:
                     text_match = re.search(r"Reading local file: (.*?)(\n|$)", output)
                     if text_match:
                         filepath = text_match.group(1).strip()
                         text_command_match = {"name": "read_local_file", "parameters": {"filepath": filepath}}
                     else:
                         # Fallback 2: "The single best matching file is: ..."
                         best_match = re.search(r"The single best matching file is: (.*?)(\n|$)", output)
                         if best_match:
                             filepath = best_match.group(1).strip()
                             # Only trigger if followed by some intent to read, or just default to reading it?
                             # Given the user flow "Summarize this...", if we found the file, we should read it.
                             text_command_match = {"name": "read_local_file", "parameters": {"filepath": filepath}}

            if json_match or text_command_match:
                print("DEBUG WORKER: Detected embedded tool call (JSON or TEXT). Intercepting...")
                try:
                    cmd = None
                    if json_match:
                        # ... (JSON parsing logic) ...
                        json_str = json_match.strip()
                        if not json_str.endswith("}"): json_str += "}"
                        if not json_str.endswith("}}"): json_str += "}"
                        cmd = json.loads(json_str)
                    elif text_command_match:
                        cmd = text_command_match
                    
                    # ... (Execute logic) ...
                    if cmd.get("name") == "search_files":
                        params = cmd.get("parameters", {})
                        query = params.get("query")
                        path = params.get("search_path")
                        if isinstance(path, dict): # Handle the weird nested dict
                             if 'search_path' in path: path = path['search_path']
                             
                        # Execute search manually
                        from agent.tools.file_search import search_files
                        tool_result = search_files.invoke({"query": query, "search_path": path})
                        
                        output = f"**(Auto-corrected)** I found these files:\n{tool_result}"
                    
                    elif cmd.get("name") == "read_local_file":
                        params = cmd.get("parameters", {})
                        # Map input args (sometimes 'fp', sometimes 'filepath')
                        fp = params.get("filepath") or params.get("fp")
                        
                        from agent.tools.doc_reader import read_local_file
                        tool_result = read_local_file.invoke({"filepath": fp})
                        
                        # STRATEGY CHANGE: "Tool" messages are being ignored.
                        # We will inject the content as a "USER/SYSTEM" message which often carries more weight.
                        
                        base_history = response['messages'][:-1]
                        
                        # 1. Fake the AI's "I am reading" step (as a thought, not a tool call) makes it cleaner
                        # Actually, let's just skip to the result.
                        
                        # 2. Construct the "System provided data" message
                        truncated_content = str(tool_result)[:20000] 
                        if len(str(tool_result)) > 20000:
                            truncated_content += "\n...[Content Truncated due to size]..."

                        if str(tool_result).startswith("Error"):
                             user_data = f"SYSTEM UPDATE: The file read failed. Error: {tool_result}. Report this to the user."
                        else:
                             user_data = (
                                 f"SYSTEM UPDATE: File '{fp}' read successfully.\n"
                                 "Here is the content you must summarize:\n"
                                 "================================================\n"
                                 f"{truncated_content}\n"
                                 "================================================\n"
                                 "INSTRUCTION: Summarize the text above. Do not include outside knowledge."
                             )

                        injection_msg = HumanMessage(content=user_data)
                        
                        # New history: Old Context -> System Injection
                        new_history = base_history + [injection_msg]

                        print("DEBUG WORKER: Re-invoking agent with USER PROXY INJECTION...")
                        final_response = self.agent_executor.invoke({"messages": new_history})
                        print(f"DEBUG WORKER: Final Summary Response: {final_response}")
                        
                        output = final_response['messages'][-1].content
                        
                except Exception as e:
                    print(f"DEBUG WORKER: Failed to parse raw JSON: {e}")
                    output += f"\n(Error processing tool: {e})"
            
            self.finished.emit(output)
        except Exception as e:
            self.error.emit(str(e))
