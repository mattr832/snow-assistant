"""
Test the avalanche forecast tool integration with the agent.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.workflow import LocalGPUAgent

print("Testing Avalanche Forecast Tool Integration")
print("=" * 80)
print()

try:
    agent = LocalGPUAgent()
    
    test_query = "What's the avalanche forecast for Stevens Pass today?"
    
    print(f"Query: {test_query}")
    print("-" * 80)
    print()
    
    response = agent.run(test_query)
    
    print(response)
    print()
    print("=" * 80)
    print("✅ Integration test completed!")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
