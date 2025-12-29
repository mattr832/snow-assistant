"""Chainlit UI with tool-enabled agent using Mistral via Ollama"""

import chainlit as cl
from chainlit.types import ThreadDict
from agents.workflow import LocalGPUAgent
from langchain_core.messages import HumanMessage, AIMessage
import logging
import time
import json
import asyncio
from scheduler import start_scheduler, stop_scheduler, get_scheduler

logger = logging.getLogger(__name__)

# Track processed Slack events to prevent duplicates
_processed_slack_events = set()
_slack_event_lock = asyncio.Lock()


def is_slack_platform() -> bool:
    """Check if the current session is from Slack"""
    return cl.user_session.get("slack_event") is not None


async def is_duplicate_slack_event() -> bool:
    """Check if this Slack event has already been processed"""
    if not is_slack_platform():
        return False
    
    slack_event = cl.user_session.get("slack_event")
    if not slack_event:
        return False
    
    # Use event_ts as unique identifier
    event_id = slack_event.get("event", {}).get("event_ts")
    if not event_id:
        return False
    
    async with _slack_event_lock:
        if event_id in _processed_slack_events:
            logger.warning(f"Duplicate Slack event detected: {event_id}")
            return True
        
        # Add to processed set (keep only last 1000 to prevent memory issues)
        _processed_slack_events.add(event_id)
        if len(_processed_slack_events) > 1000:
            _processed_slack_events.pop()
    
    return False


async def generate_weather_plots_if_needed(agent, response_message):
    """
    Generate and send weather plots if Stevens Pass weather tools were used.
    This runs in the proper async Chainlit context with access to cl.Plotly.
    Note: Skips plot generation for Slack as Plotly charts don't render in Slack.
    """
    try:
        # Skip plots for Slack platform (Plotly doesn't render well in Slack)
        if is_slack_platform():
            logger.debug("Skipping plot generation for Slack platform")
            return
        
        # Check the agent's last result state to see if Stevens Pass tools were called
        state = getattr(agent, 'last_result_state', None)
        if not state:
            logger.debug("No state found - skipping plot generation")
            return
        
        messages = state.get("messages", [])
        
        # Look for tool calls related to Stevens Pass weather
        stevens_pass_tools = ["stevens_pass_comprehensive_weather", "stevens_pass_snow_analysis"]
        tool_was_used = False
        tool_name_found = None
        
        for msg in messages:
            # Check ToolMessage which contains tool execution results
            if hasattr(msg, "name"):
                msg_name = msg.name
                logger.debug(f"Found message with name: {msg_name}")
                if msg_name in stevens_pass_tools:
                    tool_was_used = True
                    tool_name_found = msg_name
                    break
        
        if not tool_was_used:
            logger.debug(f"No Stevens Pass weather tools were used - checked {len(messages)} messages")
            return
        
        logger.info(f"✓ Detected {tool_name_found} was used - generating plots in async context")
        
        # Fetch the grid data and generate plots
        from tools.basic_tools import _fetch_stevens_pass_detailed_data, generate_stevens_pass_weather_plots
        
        data = _fetch_stevens_pass_detailed_data()
        grid_data = data.get("grid_data")
        
        if not grid_data:
            logger.warning("No grid data available for plotting")
            return
        
        # Generate plots
        plot_result = generate_stevens_pass_weather_plots(grid_data)
        
        # Create Plotly elements in the proper async context
        elements = []
        if plot_result.get("figure1"):
            logger.info("Creating Plotly element for figure1")
            elements.append(cl.Plotly(name="Precipitation & Wind", figure=plot_result["figure1"]))
        if plot_result.get("figure2"):
            logger.info("Creating Plotly element for figure2")
            elements.append(cl.Plotly(name="Temperature & Humidity", figure=plot_result["figure2"]))
        
        if elements:
            logger.info(f"Sending {len(elements)} plot elements to Chainlit")
            plot_msg = cl.Message(
                content="📊 **Stevens Pass Weather Forecast Charts**",
                elements=elements
            )
            await plot_msg.send()
            logger.info("✓ Weather plots sent successfully")
            
    except Exception as e:
        logger.error(f"Error generating weather plots: {e}", exc_info=True)


# Configure Chainlit with persistence
@cl.set_chat_profiles
async def chat_profiles():
    """Define chat profiles for different conversation modes"""
    return [
        cl.ChatProfile(
            name="Default",
            markdown_description="AI weather analyst for Stevens Pass.",
            icon="https://api.dicebear.com/7.x/thumbs/svg?seed=Chat"
        )
    ]


@cl.on_chat_start
async def start():
    """Initialize agent with tool support"""
    try:
        # Start the scheduler on first chat start (only runs once globally)
        try:
            start_scheduler()
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
        
        # Initialize agent with tools
        agent = LocalGPUAgent()
        cl.user_session.set("agent", agent)
        
        # Initialize message tracking
        cl.user_session.set("message_count", 0)
        
        # Check if running in Slack mode
        if is_slack_platform():
            slack_user = cl.user_session.get("user")
            logger.info(f"Slack session started for user: {slack_user}")
        
        # Check Ollama connection - but don't send messages yet to allow starters to show
        if not agent.llm.check_connection():
            # Show error if LLM provider is down
            provider = agent.llm.provider
            if provider == "ollama":
                await cl.Message(
                    content="⚠️ **Warning**: Cannot connect to Ollama at http://localhost:11434\n\nPlease start Ollama:\n```\nollama serve\n```",
                    metadata={"timestamp": time.time(), "type": "system"}
                ).send()
            elif provider == "openai":
                await cl.Message(
                    content="⚠️ **Warning**: Cannot connect to OpenAI API\n\nPlease check your OPENAI_API_KEY in .env file",
                    metadata={"timestamp": time.time(), "type": "system"}
                ).send()
        else:
            # Don't send welcome message - let starters show instead
            logger.info(f"Chat session started with {agent.llm.model_name} ({agent.llm.provider}) and {len(agent.tools)} tools")
        
    except Exception as e:
        logger.error(f"Error initializing agent: {e}")
        await cl.Message(
            content=f"❌ Error initializing agent: {str(e)}",
            metadata={"timestamp": time.time(), "type": "error"}
        ).send()


@cl.set_starters
async def set_starters():
    """Set starter prompts for quick access to common queries"""
    return [
        cl.Starter(
            label="❄️ Analyze Snow Forecast",
            message="Analyze the snow forecast for Stevens Pass",
            icon="",
        ),
        cl.Starter(
            label="🌡️ Current Conditions",
            message="Check the current conditions at Stevens Pass",
            icon="",
        ),
        cl.Starter(
            label="🏔️ Road Conditions",
            message="What are the current road conditions and pass status for Stevens Pass?",
            icon="",
        ),
        cl.Starter(
            label="⛅ Forecast Discussion",
            message="Get the NOAA Area Forecast Discussion for the Cascades",
            icon="",
        ),
        cl.Starter(
            label="📈 Weather Charts",
            message="Show me weather charts for Stevens Pass",
            icon="",
        ),
    ]


@cl.on_message
async def main(message: cl.Message):
    """Process user message with agent tool calling with streaming and keep-alive"""
    agent = cl.user_session.get("agent")
    
    if not agent:
        await cl.Message(
            content="❌ Agent not initialized. Please refresh the page.",
            metadata={"timestamp": time.time(), "type": "error"}
        ).send()
        return
    
    try:
        logger.info(f"User: {message.content}")
        
        # Handle Slack-specific features
        if is_slack_platform():
            # Check for duplicate event (Slack retries)
            if await is_duplicate_slack_event():
                logger.info("Ignoring duplicate Slack event")
                return
            
            slack_event = cl.user_session.get("slack_event")
            attached_files = message.elements
            if attached_files:
                logger.info(f"Received {len(attached_files)} attached files from Slack")
        
        # Get chat history in OpenAI format
        chat_history = cl.chat_context.to_openai()
        logger.info(f"Chat history has {len(chat_history)} messages")
        
        # Check LLM connection
        if not agent.llm.check_connection():
            provider = agent.llm.provider
            if provider == "ollama":
                await cl.Message(
                    content="⚠️ **Error**: Cannot connect to Ollama at http://localhost:11434\n\nPlease start Ollama in another terminal:\n```\nollama serve\n```\n\nThen try your message again.",
                    metadata={"timestamp": time.time(), "type": "error"}
                ).send()
            elif provider == "openai":
                await cl.Message(
                    content="⚠️ **Error**: Cannot connect to OpenAI API\n\nPlease check your OPENAI_API_KEY in .env file",
                    metadata={"timestamp": time.time(), "type": "error"}
                ).send()
            return
        
        # Create a message to display the response
        response_message = cl.Message(content="")
        await response_message.send()
        
        start_time = time.time()
        
        # Create a thread-safe streaming callback
        # We need this because the LLM runs in a thread pool but we need to call async functions
        import threading
        
        loop = asyncio.get_event_loop()
        stream_futures = []  # Track all streaming futures
        stream_errors = []
        context_error_logged = False  # Track if we've logged context errors
        futures_lock = threading.Lock()  # Thread-safe access to futures list
        
        def stream_callback(token: str):
            """Thread-safe callback that schedules async streaming"""
            nonlocal context_error_logged
            try:
                # Schedule the coroutine and track the future
                future = asyncio.run_coroutine_threadsafe(
                    response_message.stream_token(token),
                    loop
                )
                with futures_lock:
                    stream_futures.append(future)
            except Exception as e:
                error_msg = str(e)
                with futures_lock:
                    stream_errors.append(error_msg)
                # Only log context errors once to avoid spam
                if ("context" in error_msg.lower() or "chainlit" in error_msg.lower()):
                    if not context_error_logged:
                        logger.warning(f"⚠️ Chainlit context not available for streaming (thread pool limitation) - will use fallback")
                        context_error_logged = True
                else:
                    logger.error(f"Stream callback scheduling error: {e}")
        
        # Run the agent with async streaming
        final_response = await agent.run_async(
            message.content,
            chat_history=chat_history,
            stream_callback=stream_callback
        )
        
        # Wait for all streaming to complete before proceeding
        # Make a copy of futures list to avoid holding lock during wait
        with futures_lock:
            futures_to_wait = list(stream_futures)
            errors_count = len(stream_errors)
        
        successful_streams = 0
        context_errors = 0
        if futures_to_wait:
            logger.debug(f"Waiting for {len(futures_to_wait)} streaming operations to complete")
            for future in futures_to_wait:
                try:
                    # Wait for each future with a reasonable timeout
                    future.result(timeout=5.0)
                    successful_streams += 1
                except Exception as e:
                    # Check if it's a Chainlit context error (streaming from thread pool issue)
                    error_msg = str(e)
                    if "context" in error_msg.lower() or "chainlit" in error_msg.lower():
                        # This is expected when streaming from thread pool - will use fallback
                        context_errors += 1
                    else:
                        logger.error(f"Stream future error: {e}")
                        with futures_lock:
                            stream_errors.append(str(e))
            
            if successful_streams > 0:
                logger.debug(f"✓ Streaming complete: {successful_streams}/{len(futures_to_wait)} successful")
            elif context_errors > 0:
                logger.info(f"⚠️ Streaming failed due to Chainlit context ({context_errors} tokens) - using fallback")
            else:
                logger.warning(f"⚠️ Streaming failed: {len(stream_errors)} errors")
        
        # If streaming failed (no successful streams), set content as fallback
        with futures_lock:
            total_errors = len(stream_errors)
            total_futures = len(stream_futures)
        
        if successful_streams == 0 and total_futures > 0:
            # Complete streaming failure - set content as fallback
            response_message.content = final_response
            await response_message.update()
        elif 0 < successful_streams < total_futures:
            # Partial streaming success - ensure complete content is set
            logger.info(f"Partial streaming: {successful_streams}/{total_futures} tokens displayed, updating full content")
            response_message.content = final_response
            await response_message.update()
        
        elapsed_time = time.time() - start_time
        
        # Check if Stevens Pass weather tools were used and generate plots
        # This runs in the proper async Chainlit context
        await generate_weather_plots_if_needed(agent, response_message)
        
        # Update metadata
        response_message.metadata = {
            "timestamp": time.time(),
            "type": "assistant",
            "model": agent.llm.model_name,
            "response_time_seconds": round(elapsed_time, 2),
        }
        await response_message.update()
        
        message_count = cl.user_session.get("message_count", 0) + 1
        cl.user_session.set("message_count", message_count)
        
        logger.info(f"Response complete in {elapsed_time:.2f}s")
        
    except asyncio.TimeoutError:
        logger.error("Response processing timed out")
        await cl.Message(
            content="⏱️ **Timeout**: The analysis took too long to process. Please try again or use a simpler query.",
            metadata={"timestamp": time.time(), "type": "error"}
        ).send()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        await cl.Message(
            content=f"❌ Error: {str(e)}",
            metadata={"timestamp": time.time(), "type": "error"}
        ).send()


@cl.on_chat_end
async def on_chat_end():
    """Handle chat session end - optional cleanup"""
    message_count = cl.user_session.get("message_count", 0)
    logger.info(f"Chat session ended. Total messages exchanged: {message_count}")


@cl.on_stop
async def on_stop():
    """Handle when user clicks stop button during task execution"""
    logger.info("User requested to stop the current task")
    # You could add logic here to cancel ongoing operations if needed


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    """Handle when user resumes a previous chat session"""
    logger.info(f"User resumed chat session: {thread.get('id', 'unknown')}")
    
    # Reinitialize the agent
    agent = LocalGPUAgent()
    cl.user_session.set("agent", agent)
    
    # Restore message count if available in thread metadata
    message_count = len(thread.get("steps", []))
    cl.user_session.set("message_count", message_count)
    
    logger.info(f"Restored chat session with {message_count} messages")


# ============================================================================
# Scheduler Management
# ============================================================================

def get_scheduler_status():
    """Get scheduler status information"""
    scheduler = get_scheduler()
    if scheduler.is_running:
        next_run = scheduler.get_next_run_time()
        return {
            "running": True,
            "next_run": str(next_run) if next_run else "Unknown",
            "channel": scheduler.slack_channel
        }
    return {"running": False}


# Cleanup on app shutdown
import atexit
atexit.register(stop_scheduler)

