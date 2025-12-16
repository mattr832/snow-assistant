"""Agentic workflow using LangGraph with unified LLM (Ollama or OpenAI)"""

from typing import Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from models.local_llm import UnifiedLLM
from tools.basic_tools import tools, get_tool_by_name
import json
import logging
import uuid

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State definition for the agent"""
    messages: list[BaseMessage]
    current_tool: str | None
    tool_input: dict | None
    tool_call_id: str | None


class LocalGPUAgent:
    """Agentic workflow using LangGraph with unified LLM"""

    def __init__(self):
        self.llm = UnifiedLLM()
        self.tools = tools
        self.graph = None
        self._build_graph()

    def _build_graph(self):
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tool_use", self._tool_use_node)
        workflow.add_node("end", self._end_node)

        # Add edges
        workflow.add_edge("agent", "tool_use")
        workflow.add_conditional_edges(
            "tool_use",
            self._should_continue,
            {
                "continue": "agent",  # After tool execution, go back to agent to process result
                "end": "end",          # If no tool was executed, go to end
            },
        )

        workflow.set_entry_point("agent")
        self.graph = workflow.compile()

    def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node - decides what to do next"""
        logger.info("📊 Agent node: Reasoning...")

        # Format messages for the LLM
        messages = state["messages"]
        
        # Create a prompt with tools description
        tools_description = self._format_tools()
        system_prompt = f"""You are a helpful AI assistant with expertise in weather and mountain forecasting. You can access specialized tools for Stevens Pass weather analysis, or provide general information and conversation.

You have access to the following tools when needed:

{tools_description}

CRITICAL TOOL USAGE RULES:
1. When calling a tool, respond with ONLY a valid JSON object in this exact format:
   {{"action": "tool_name", "input": {{...parameters...}}}}
   
2. IMPORTANT: Read each tool description carefully!
   - If description says "REQUIRES parameter" → include the parameter in input
   - If description says "NO parameters needed" → use empty object: "input": {{}}
   
3. Tool calling examples:
   
   Tools WITH parameters (MUST include the parameter):
   - search needs 'query': {{"action": "search", "input": {{"query": "powder skiing"}}}}
   
   Tools WITHOUT parameters (MUST use empty input {{}}):
   - {{"action": "nwac_avalanche_forecast", "input": {{}}}}
   - {{"action": "noaa_area_forecast_discussion", "input": {{}}}}
   - {{"action": "stevens_pass_comprehensive_weather", "input": {{}}}}
   - {{"action": "stevens_pass_snow_analysis", "input": {{}}}}
   - {{"action": "powder_poobah_forecast", "input": {{}}}}

4. For general questions or conversation, provide your answer directly without any JSON.

5. When you receive tool results (marked as [Tool Result from tool_name]), synthesize the information and present it clearly to the user. DO NOT call the same tool again unless the user explicitly asks for updated information.

6. Be helpful, conversational, and informative."""

        # Build conversation history for prompt
        # Only include recent conversation to avoid confusion from old tool calls
        conversation = []
        
        # Get last N messages (limit to prevent context overflow and confusion)
        recent_messages = messages[-10:] if len(messages) > 10 else messages
        
        for msg in recent_messages:
            if isinstance(msg, HumanMessage):
                conversation.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                # Skip system/welcome messages that aren't relevant to current conversation
                if "Connected to" not in msg.content and "Tools Available" not in msg.content:
                    conversation.append(f"Assistant: {msg.content}")
            elif isinstance(msg, ToolMessage):
                # Add tool results as context for the LLM to synthesize
                tool_name = getattr(msg, 'name', 'unknown_tool')
                # Truncate very long tool results to keep prompt manageable
                tool_content = msg.content[:1000] + "...[truncated]" if len(msg.content) > 1000 else msg.content
                conversation.append(f"[Tool Result from {tool_name}]: {tool_content}")
        
        conversation_text = "\n\n".join(conversation) if conversation else "User: Hello"
        
        # Check if we just received a tool result - if so, prompt LLM to synthesize it
        if messages and isinstance(messages[-1], ToolMessage):
            additional_instruction = "\n\nThe tool has returned results above. Please synthesize this information and provide a clear, helpful response to the user. Present the key information in a well-formatted way."
            prompt = f"{system_prompt}\n\n{conversation_text}{additional_instruction}\n\nAssistant:"
        else:
            prompt = f"{system_prompt}\n\n{conversation_text}\n\nAssistant:"
        
        # DEBUG: Log the prompt being sent to LLM
        logger.debug(f"📝 PROMPT SENT TO LLM:\n{prompt[:500]}...")
        
        response_chunks = []
        for chunk in self.llm.generate_stream(prompt):
            response_chunks.append(chunk)
        
        response = "".join(response_chunks)
        
        # DEBUG: Log full response for inspection
        logger.info(f"💭 LLM Response (full): {response}")
        logger.info(f"💭 Response length: {len(response)} chars")
        logger.info(f"💭 Response starts with {{: {response.strip().startswith('{')}")
        logger.info(f"💭 Response first 200 chars: {response[:200]}...")

        # Check if response is a tool call (starts with {)
        current_tool = None
        tool_input = None
        tool_call_id = None
        
        try:
            response_stripped = response.strip()
            logger.debug(f"🔍 Checking for tool call, stripped response: {response_stripped[:100]}...")
            
            if response_stripped.startswith('{'):
                logger.info("✅ Response starts with {{, attempting JSON parse...")
                # Try to extract JSON
                import re
                json_match = re.search(r'\{.*\}', response_stripped, re.DOTALL)
                if json_match:
                    logger.debug(f"📦 JSON match found: {json_match.group()[:100]}...")
                    tool_call = json.loads(json_match.group())
                    action = tool_call.get("action")
                    logger.debug(f"🎯 Extracted action: {action}")
                    
                    # Only treat as tool call if action is a real tool (not "response")
                    if action and action != "response" and get_tool_by_name(action):
                        current_tool = action
                        tool_input = tool_call.get("input", {})
                        tool_call_id = str(uuid.uuid4())  # Generate unique tool call ID
                        logger.info(f"🔧 Detected tool call: {action} (ID: {tool_call_id})")
                    else:
                        logger.info(f"❌ Action '{action}' is not a valid tool or is 'response'")
                else:
                    logger.warning(f"⚠️ Response starts with {{ but no JSON match found in: {response_stripped[:200]}...")
            else:
                logger.debug(f"❌ Response does NOT start with {{, first char is: '{response_stripped[0] if response_stripped else 'EMPTY'}'")
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"❌ JSON parse error: {e}. Response was: {response_stripped[:200]}...")

        # If this is a tool call, don't add the JSON to messages
        # The tool result will be added later
        if current_tool:
            return {
                "messages": messages,  # Don't add the JSON tool call to messages
                "current_tool": current_tool,
                "tool_input": tool_input,
                "tool_call_id": tool_call_id,
            }
        
        # For normal responses, add to messages
        return {
            "messages": messages + [AIMessage(content=response)],
            "current_tool": None,
            "tool_input": None,
            "tool_call_id": None,
        }

    def _tool_use_node(self, state: AgentState) -> AgentState:
        """Tool execution node"""
        if not state["current_tool"]:
            return {
                "messages": state["messages"],
                "current_tool": None,
                "tool_input": None,
                "tool_call_id": None,
            }

        logger.info(f"🔧 Using tool: {state['current_tool']}")

        tool = get_tool_by_name(state["current_tool"])
        tool_call_id = state.get("tool_call_id", str(uuid.uuid4()))
        
        if not tool:
            error_msg = f"Tool '{state['current_tool']}' not found"
            logger.error(f"✗ {error_msg}")
            return {
                "messages": state["messages"] + [ToolMessage(content=error_msg, tool_call_id=tool_call_id)],
                "current_tool": None,
                "tool_input": None,
                "tool_call_id": None,
            }

        try:
            # Execute tool
            tool_input = state["tool_input"] or {}
            if isinstance(tool_input, dict):
                result = tool.func(**tool_input)
            else:
                result = tool.func(tool_input)
            
            result_str = str(result)
            
            # Log result (truncated for display)
            result_preview = result_str[:200] if len(result_str) > 200 else result_str
            logger.info(f"✓ Tool result: {result_preview}...")
            
            # For long results (analysis, forecasts), show progress
            if len(result_str) > 500:
                logger.info(f"📊 Tool returned {len(result_str)} characters of analysis")
            
            # Create ToolMessage with the tool name for tracking
            tool_message = ToolMessage(
                content=result_str, 
                tool_call_id=tool_call_id,
                name=state["current_tool"]  # Add tool name for identification
            )
            
            return {
                "messages": state["messages"] + [tool_message],
                "current_tool": None,
                "tool_input": None,
                "tool_call_id": None,
            }
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            logger.error(f"✗ {error_msg}")
            return {
                "messages": state["messages"] + [ToolMessage(content=error_msg, tool_call_id=tool_call_id)],
                "current_tool": None,
                "tool_input": None,
                "tool_call_id": None,
            }

    def _end_node(self, state: AgentState) -> AgentState:
        """End node - prepares final response"""
        logger.info("✓ Agent workflow completed")
        
        # Extract tool results if any
        messages = state["messages"]
        tool_results = []
        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_results.append(msg.content)
        
        # If we have tool results, they should be included in the final response
        if tool_results and messages:
            # The last message should contain the tool result
            logger.info(f"📊 Returning {len(tool_results)} tool result(s)")
        
        return {
            "messages": messages,
            "current_tool": None,
            "tool_input": None,
            "tool_call_id": None,
        }

    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue or end
        
        Returns "continue" if:
        - A tool call was detected and needs execution OR
        - Tool just executed and result needs to be synthesized
        
        Returns "end" if:
        - No tool detected and last message is from assistant (normal response)
        """
        messages = state["messages"]
        
        # If current_tool is set, we need to execute it
        if state["current_tool"]:
            return "continue"
        
        # If the last message is a ToolMessage, go back to agent to synthesize
        if messages and isinstance(messages[-1], ToolMessage):
            logger.info("🔄 Tool result received - routing back to agent for synthesis")
            return "continue"
        
        # Otherwise, we're done
        return "end"

    def _format_tools(self) -> str:
        """Format tools description for LLM"""
        descriptions = []
        for tool in self.tools:
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)

    def run(self, user_input: str) -> str:
        """Run the agent with user input"""
        logger.info(f"🚀 Starting agent workflow with input: {user_input}")
        
        # Check LLM provider connection
        if not self.llm.check_connection():
            provider = self.llm.provider
            if provider == "ollama":
                return "Error: Cannot connect to Ollama. Please start Ollama with: ollama serve"
            elif provider == "openai":
                return "Error: Cannot connect to OpenAI API. Please check your OPENAI_API_KEY in .env"
            else:
                return f"Error: Cannot connect to LLM provider: {provider}"

        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "current_tool": None,
            "tool_input": None,
            "tool_call_id": None,
        }

        result = self.graph.invoke(initial_state)
        
        # Extract final response - look for the last AIMessage (excluding welcome messages)
        final_response = None
        if result["messages"]:
            # Traverse messages in reverse to find the last AIMessage
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    # Skip system/welcome messages
                    if "Connected to" not in msg.content and "Tools Available" not in msg.content:
                        final_response = msg.content
                        break
            
            # If no AIMessage found, check for ToolMessage as fallback
            if not final_response:
                for msg in reversed(result["messages"]):
                    if isinstance(msg, ToolMessage):
                        final_response = msg.content
                        break
            
            # Last resort: get the last message's content
            if not final_response and result["messages"]:
                final_response = result["messages"][-1].content
        
        if not final_response:
            final_response = "No response generated"
        
        logger.info(f"✓ Final response extracted: {final_response[:100]}...")
        return final_response

    async def run_async(self, user_input: str, chainlit_message: Any = None, chat_history: list = None) -> str:
        """Run the agent with user input and stream results to Chainlit
        
        Args:
            user_input: User's input message
            chainlit_message: Optional Chainlit message object to update with streaming results
            chat_history: Optional list of previous messages in OpenAI format
            
        Returns:
            Final response text
        """
        import asyncio
        
        try:
            import chainlit as cl
        except ImportError:
            chainlit_message = None
        
        logger.info(f"🚀 Starting agent workflow with input: {user_input}")
        
        # Check LLM provider connection
        if not self.llm.check_connection():
            provider = self.llm.provider
            if provider == "ollama":
                return "Error: Cannot connect to Ollama. Please start Ollama with: ollama serve"
            elif provider == "openai":
                return "Error: Cannot connect to OpenAI API. Please check your OPENAI_API_KEY in .env"
            else:
                return f"Error: Cannot connect to LLM provider: {provider}"

        # Convert chat history from OpenAI format to LangChain messages
        messages = []
        if chat_history:
            for msg in chat_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
            logger.info(f"📝 Loaded {len(messages)} messages from chat history")
        else:
            # No history, just add current message
            messages = [HumanMessage(content=user_input)]

        initial_state = {
            "messages": messages,
            "current_tool": None,
            "tool_input": None,
            "tool_call_id": None,
        }

        try:
            # Send status update before starting
            if chainlit_message:
                chainlit_message.content = "🧠 Thinking..."
                await chainlit_message.update()
            
            # Run the graph in a thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Create a task to periodically update status
            async def update_status():
                """Periodically update status while processing"""
                start = asyncio.get_event_loop().time()
                while True:
                    await asyncio.sleep(3)
                    if chainlit_message:
                        elapsed = int(asyncio.get_event_loop().time() - start)
                        chainlit_message.content = f"⏳ Processing... ({elapsed}s)"
                        await chainlit_message.update()
            
            # Start status update task
            status_task = asyncio.create_task(update_status())
            
            try:
                # Run the blocking graph.invoke in a thread pool
                result = await loop.run_in_executor(None, self.graph.invoke, initial_state)
                
                # Store the result state for later access (e.g., for plot generation)
                self.last_result_state = result
            finally:
                # Cancel status updates
                status_task.cancel()
                try:
                    await status_task
                except asyncio.CancelledError:
                    pass
            
            # Extract final response - look for the last AIMessage (excluding welcome messages)
            final_response = None
            if result["messages"]:
                # Traverse messages in reverse to find the last AIMessage
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage):
                        # Skip system/welcome messages
                        if "Connected to" not in msg.content and "Tools Available" not in msg.content:
                            final_response = msg.content
                            break
                
                # If no AIMessage found, check for ToolMessage as fallback
                if not final_response:
                    for msg in reversed(result["messages"]):
                        if isinstance(msg, ToolMessage):
                            final_response = msg.content
                            break
                
                # Last resort: get the last message's content
                if not final_response and result["messages"]:
                    final_response = result["messages"][-1].content
            
            if not final_response:
                final_response = "No response generated"
            
            logger.info(f"✓ Final response extracted: {final_response[:150]}...")
            
            # Update Chainlit message with the final response
            if chainlit_message:
                chainlit_message.content = final_response
                await chainlit_message.update()
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            if chainlit_message:
                chainlit_message.content = f"❌ Error: {str(e)}"
                await chainlit_message.update()
            raise


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    agent = LocalGPUAgent()
    response = agent.run("What is 25 * 4?")
    print(f"\nFinal Response: {response}")
