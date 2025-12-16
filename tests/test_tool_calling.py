"""
Test suite to diagnose tool calling issues in the agent workflow.

This test suite checks:
1. Tool definitions are properly structured
2. LLM can understand and respond to tool requests
3. JSON parsing and tool detection works correctly
4. Agent workflow properly routes tool calls
"""

import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.basic_tools import tools, get_tool_by_name
from models.local_llm import UnifiedLLM
from agents.workflow import LocalGPUAgent
import logging

# Configure logging to see debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_tool_definitions():
    """Test 1: Verify tool definitions are correct"""
    print("\n" + "="*80)
    print("TEST 1: Tool Definitions")
    print("="*80)
    
    print(f"\nTotal tools defined: {len(tools)}")
    
    for tool in tools:
        print(f"\n✓ Tool: {tool.name}")
        print(f"  Description: {tool.description[:100]}...")
        print(f"  Function: {tool.func.__name__}")
        
        # Check if tool is callable
        assert callable(tool.func), f"Tool {tool.name} function is not callable"
    
    print("\n✅ All tool definitions are valid")


def test_tool_execution():
    """Test 2: Verify tools can execute directly"""
    print("\n" + "="*80)
    print("TEST 2: Direct Tool Execution")
    print("="*80)
    
    # Test get_tool_by_name with a valid tool
    print("\n📝 Testing get_tool_by_name('search')...")
    tool = get_tool_by_name("search")
    assert tool is not None, "get_tool_by_name failed"
    assert tool.name == "search", f"Wrong tool returned: {tool.name}"
    print(f"   ✅ get_tool_by_name works: {tool.name}")
    
    print("\n✅ All tool lookup functions work correctly")


def test_llm_connection():
    """Test 3: Verify LLM connection and basic generation"""
    print("\n" + "="*80)
    print("TEST 3: LLM Connection")
    print("="*80)
    
    try:
        llm = UnifiedLLM()
        print(f"\n✓ LLM initialized: {llm.provider} provider")
        
        if llm.provider == "ollama":
            from config import OLLAMA_MODEL_NAME
            print(f"  Model: {OLLAMA_MODEL_NAME}")
        elif llm.provider == "openai":
            from config import OPENAI_MODEL_NAME
            print(f"  Model: {OPENAI_MODEL_NAME}")
        
        # Check connection
        is_connected = llm.check_connection()
        status = '✅ Connected' if is_connected else '❌ Not connected'
        print(f"✓ Connection status: {status}")
        
        if not is_connected:
            if llm.provider == "ollama":
                print("\n⚠️ WARNING: Ollama is not running. Start it with: ollama serve")
            elif llm.provider == "openai":
                print("\n⚠️ WARNING: Cannot reach OpenAI API. Check your API key in .env")
            print("   Skipping LLM generation tests...")
            return False
        
        # Test basic generation
        print("\n📝 Testing basic LLM generation...")
        prompt = "What is 2 + 2? Answer with just the number."
        response = llm.generate(prompt)
        print(f"   Prompt: {prompt}")
        print(f"   Response: {response[:200]}")
        print("   ✅ LLM generation works")
        
        return True
        
    except Exception as e:
        print(f"\n❌ LLM test failed: {e}")
        return False


def test_llm_tool_calling_simple():
    """Test 4: Test if LLM can generate JSON for simple tool calls"""
    print("\n" + "="*80)
    print("TEST 4: LLM Tool Calling (Simple Test)")
    print("="*80)
    
    try:
        llm = UnifiedLLM()
        
        if not llm.check_connection():
            print("\n⚠️ Skipping - LLM not connected")
            return
        
        # Create a VERY explicit prompt for tool calling
        prompt = """You are a helpful AI assistant. When you need to use a tool, you MUST respond with ONLY a JSON object in this exact format:
{"action": "tool_name", "input": {"parameter": "value"}}

You have access to this tool:
- search: Search for general information on any topic. REQUIRES parameter 'query'. Example: {"action": "search", "input": {"query": "skiing conditions"}}

User: Search for information about powder skiing.

Now respond with ONLY the JSON to call the search tool. Do not include any other text."""

        print("\n📝 Sending test prompt to LLM...")
        print(f"Prompt length: {len(prompt)} chars")
        
        response = llm.generate(prompt)
        
        print(f"\n💭 LLM Response:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        
        # Check if response is JSON
        response_stripped = response.strip()
        print(f"\n🔍 Analysis:")
        print(f"   Response length: {len(response_stripped)} chars")
        print(f"   Starts with '{{': {response_stripped.startswith('{')}")
        print(f"   First 50 chars: {response_stripped[:50]}")
        
        if response_stripped.startswith('{'):
            print("   ✅ Response starts with JSON bracket")
            
            # Try to parse JSON
            try:
                import re
                json_match = re.search(r'\{.*\}', response_stripped, re.DOTALL)
                if json_match:
                    tool_call = json.loads(json_match.group())
                    print(f"   ✅ Valid JSON parsed")
                    print(f"   Action: {tool_call.get('action')}")
                    print(f"   Input: {tool_call.get('input')}")
                    
                    # Verify it's the search tool
                    if tool_call.get('action') == 'search':
                        print("   ✅ Correctly identified search tool")
                    else:
                        print(f"   ❌ Wrong action: {tool_call.get('action')}")
                else:
                    print("   ❌ No JSON match found in response")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parse error: {e}")
        else:
            print(f"   ❌ Response does NOT start with '{{' - LLM is not following tool calling format")
            print(f"   This indicates the model may not be suitable for structured tool calling.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


def test_json_detection_regex():
    """Test 5: Verify the JSON detection regex pattern works"""
    print("\n" + "="*80)
    print("TEST 5: JSON Detection Regex")
    print("="*80)
    
    import re
    
    # Test cases
    test_cases = [
        # (input, should_match, description)
        ('{"action": "search", "input": {"query": "skiing"}}', True, "Simple tool call"),
        ('  {"action": "search", "input": {"query": "skiing"}}  ', True, "Tool call with whitespace"),
        ('According to the data, {"action": "search", "input": {"query": "test"}}', False, "JSON in middle of text"),
        ('{"action": "stevens_pass_comprehensive_weather", "input": {}}', True, "Tool with empty input"),
        ('Some text before\n{"action": "search", "input": {"query": "skiing"}}', False, "Text before JSON"),
        ('Just plain text without JSON', False, "No JSON"),
    ]
    
    print("\n📝 Testing JSON detection pattern:")
    
    for test_input, should_match, description in test_cases:
        response_stripped = test_input.strip()
        starts_with_brace = response_stripped.startswith('{')
        
        json_match = None
        parsed_ok = False
        
        if starts_with_brace:
            json_match = re.search(r'\{.*\}', response_stripped, re.DOTALL)
            if json_match:
                try:
                    tool_call = json.loads(json_match.group())
                    parsed_ok = True
                except json.JSONDecodeError:
                    parsed_ok = False
        
        matches = starts_with_brace and parsed_ok
        status = "✅" if matches == should_match else "❌"
        
        print(f"\n{status} {description}")
        print(f"   Input: {test_input[:60]}...")
        print(f"   Expected match: {should_match}, Got: {matches}")
        print(f"   Starts with '{{': {starts_with_brace}")
        if json_match:
            print(f"   Regex matched: Yes")
            print(f"   Valid JSON: {parsed_ok}")


def test_agent_workflow_simple():
    """Test 6: Test the full agent workflow with a simple request"""
    print("\n" + "="*80)
    print("TEST 6: Full Agent Workflow (Weather Query Test)")
    print("="*80)
    
    try:
        agent = LocalGPUAgent()
        
        if not agent.llm.check_ollama_connection():
            print("\n⚠️ Skipping - Ollama not running")
            return
        
        print("\n📝 Testing agent with: 'What is 25 * 4?'")
        print("   This should call a weather tool...")
        
        # Enable debug logging temporarily
        logging.getLogger('agents.workflow').setLevel(logging.DEBUG)
        
        result = agent.run("What is 25 * 4?")
        
        print(f"\n💭 Final Result:")
        print("-" * 80)
        print(result)
        print("-" * 80)
        
        # Check if result contains "100"
        if "100" in result:
            print("\n✅ Agent successfully calculated 25 * 4 = 100")
        else:
            print("\n❌ Agent did not return correct answer (expected 100)")
        
    except Exception as e:
        print(f"\n❌ Agent workflow test failed: {e}")
        import traceback
        traceback.print_exc()


def run_all_tests():
    """Run all diagnostic tests"""
    print("\n" + "="*80)
    print("TOOL CALLING DIAGNOSTIC TEST SUITE")
    print("="*80)
    print("\nThis test suite will diagnose issues with tool calling in the agent workflow.")
    
    try:
        # Test 1: Tool definitions
        test_tool_definitions()
        
        # Test 2: Tool execution
        test_tool_execution()
        
        # Test 3: LLM connection
        llm_ok = test_llm_connection()
        
        # Test 4: LLM tool calling (only if LLM is connected)
        if llm_ok:
            test_llm_tool_calling_simple()
        
        # Test 5: JSON regex
        test_json_detection_regex()
        
        # Test 6: Full agent workflow (only if LLM is connected)
        if llm_ok:
            test_agent_workflow_simple()
        
        print("\n" + "="*80)
        print("TEST SUITE COMPLETE")
        print("="*80)
        print("\nReview the output above to identify issues with tool calling.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
