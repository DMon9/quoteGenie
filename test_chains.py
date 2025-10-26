"""
Quick test of ai_chain and phase_chain to verify Ollama integration
"""
import os
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11435"
os.environ["OLLAMA_MODEL"] = "llama3.2:1b"

from orchestrator.ai_chain import generate_structured_estimate
from orchestrator.phase_chain import generate_project_phases

print("Testing ai_chain.generate_structured_estimate...")
try:
    result = generate_structured_estimate("Install a new kitchen faucet")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting phase_chain.generate_project_phases...")
try:
    result = generate_project_phases("Install a new kitchen faucet")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
