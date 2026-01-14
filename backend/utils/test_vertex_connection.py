import sys
import os
sys.path.append(os.getcwd())
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables.")
except ImportError:
    print("python-dotenv not found, environment variables might be missing.")

import asyncio
from utils.vertex_autogen_client import VertexGenAIClient
from autogen_core.models._types import UserMessage

async def test_vertex_ai():
    print("Testing VertexGenAIClient...")
    
    try:
        # Initialize client
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-001")
        client = VertexGenAIClient(model=model_name)
        print(f"Client initialized with model: {client.model_name}")
        
        # Create a test message
        messages = [
            UserMessage(content="Hello! Are you working correctly with Vertex AI? Answer with YES or NO.", source="user")
        ]
        
        # Call create
        print("Sending request to Vertex AI...")
        response = await client.create(messages=messages)
        
        print("-" * 20)
        print(f"Response: {response.content}")
        print("-" * 20)
        
        if response.content:
            print("SUCCESS: Vertex AI generated a response.")
        else:
            print("FAILURE: Empty response.")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_vertex_ai())
