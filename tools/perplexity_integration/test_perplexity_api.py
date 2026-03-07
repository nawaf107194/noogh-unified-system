import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

def call_perplexity_api(mcp_output: str, user_query: str) -> str:
    """
    Sends the output of a local MCP tool along with a user query to the Perplexity API.
    """
    if not PERPLEXITY_API_KEY:
        raise ValueError("PERPLEXITY_API_KEY environment variable not set. Please set it in your .env file or export it.")

    url = "https://api.perplexity.ai/chat/completions"

    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant connected to a local system via MCP tools. Analyze the provided local system data and answer the user's query."
            },
            {
                "role": "user",
                "content": f"Local System Data:\n{mcp_output}\n\nUser Query:\n{user_query}"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }

    print(f"Sending request to Perplexity API...")
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        print(f"Error from Perplexity API: {response.status_code}")
        print(response.text)
        return f"Error: {response.status_code}"

if __name__ == "__main__":
    # Example usage:
    # 1. Simulate getting output from your local MCP server
    # mcp_response = call_tool("get_system_health") # Replace with your actual MCP call
    
    sample_mcp_output = json.dumps({
        "status": "online",
        "cpu_usage": "45%",
        "memory_usage": "60%",
        "active_agents": 3
    }, indent=2)

    print(f"--- Simulated MCP Output ---\n{sample_mcp_output}\n---------------------------\n")

    user_question = "Based on the system data, is everything running smoothly?"
    
    print(f"User Question: {user_question}\n")

    try:
        reply = call_perplexity_api(mcp_output=sample_mcp_output, user_query=user_question)
        print("--- Perplexity API Response ---")
        print(reply)
        print("-------------------------------")
    except Exception as e:
        print(f"An error occurred: {e}")
