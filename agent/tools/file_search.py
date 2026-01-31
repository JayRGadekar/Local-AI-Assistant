import os
import fnmatch
from typing import List, Optional, Union, Dict, Any
from langchain_core.tools import tool

@tool
def search_files(query: str, search_path: Optional[Union[str, Dict[str, Any]]] = None) -> List[str]:
    """
    Search for files matching the query in the specified directory.
    
    Args:
        query: The keyword to search for in filenames (e.g. "Amazon").
        search_path: Optional directory to search in (e.g. "Downloads", "Documents"). Defaults to user home.
    """
    print(f"DEBUG TOOL: search_files called with query='{query}', search_path='{search_path}'")
    
    # FIX: Immediate unwrap if search_path is a dict
    if isinstance(search_path, dict):
        if 'search_path' in search_path:
            search_path = search_path['search_path']
        else:
            for v in search_path.values():
                if isinstance(v, str):
                    search_path = v
                    break
    
    # Ensure it's a string now
    if search_path is not None:
         search_path = str(search_path)
    
    # Handle common aliases
    if search_path:
        search_path_lower = str(search_path).lower()
        user_home = os.path.expanduser("~")
        common_dirs = {
            "downloads": os.path.join(user_home, "Downloads"),
            "documents": os.path.join(user_home, "Documents"),
            "desktop": os.path.join(user_home, "Desktop"),
            "music": os.path.join(user_home, "Music"),
            "videos": os.path.join(user_home, "Videos"),
            "pictures": os.path.join(user_home, "Pictures")
        }
        
        # Check alias match
        for key, val in common_dirs.items():
            if key in search_path_lower and (len(search_path_lower) == len(key) or not os.path.isabs(search_path)):
                search_path = val
                break

    # FALLBACK: If path still doesn't exist (e.g. /home/user/downloads), try to save it
    if search_path and not os.path.exists(search_path):
        # Heuristic: if "download" is in the bad path, use real Downloads
        if "download" in str(search_path).lower():
             search_path = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
             # Default to Home if bad path provided
             search_path = os.path.expanduser("~")

    if search_path is None:
        search_path = os.path.expanduser("~")
    
    if not os.path.exists(search_path):
        return [f"Error: Directory {search_path} does not exist."]

    results = []
    query_terms = query.lower().split()
    
    for root, dirs, files in os.walk(search_path):
        # Skip hidden and system dirs
        dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() not in ('appdata', 'windows', 'program files', 'program files (x86)')]
        
        for file in files:
            file_lower = file.lower()
            # Calculate match score: how many query terms are in the filename?
            score = sum(1 for term in query_terms if term in file_lower)
            
            # If at least one term matches, keep it
            if score > 0:
                results.append((score, os.path.join(root, file)))
        
        # Performance safety: if we have too many candidates, maybe stop? 
        # But we need to sort them first. Let's cap at 1000 candidates then sort.
        if len(results) >= 1000:
            break
    
    
    # Sort by score (descending)
    results.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 5 filenames only to avoid confusing the agent with too much noise
    final_results = [r[1] for r in results[:5]]
    
    return final_results

# Wrapper for LangChain if needed, but for now just the function
