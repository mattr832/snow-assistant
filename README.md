# ❄️ Snow Assistant

AI-powered snow forecast analyst for Stevens Pass, built with LangChain, LangGraph, and Chainlit. Get comprehensive snow forecasts, weather analysis, and avalanche safety information through an intelligent conversational interface.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-latest-green.svg)
![Chainlit](https://img.shields.io/badge/Chainlit-2.3+-orange.svg)

## 🎯 Features

### 📊 Comprehensive Weather Analysis
- **Multi-Source Data Integration**: NOAA Weather API, Northwest Avalanche Center (NWAC), Powder Poobah professional forecasts
- **Interactive Visualizations**: Plotly charts for precipitation, temperature, wind, and visibility
- **Temporal Breakdown**: Hour-by-hour and day-by-day forecast analysis
- **Expert Insights**: Reconciles professional forecaster predictions with raw NOAA data

### 🏔️ Stevens Pass Specialization
- **Location-Specific**: Tye Mill (STS54) at 5,180 ft elevation (47.7462°N, 121.0859°W)
- **Dual WFO Coverage**: Both OTX (Spokane/East Cascades) and SEW (Seattle/West Cascades) forecasts
- **Avalanche Safety**: Direct NWAC forecast integration with safety reminders
- **Powder Day Detection**: Automatically identifies 9+ inch snowfall events

### 🤖 Agentic Architecture
- **LangGraph State Machine**: Multi-step reasoning with tool execution loops
- **Streaming Responses**: Real-time token streaming with fallback handling
- **Tool-Calling Agent**: Dynamic tool selection based on user queries
- **Chat History**: Maintains context across conversations

## 🛠️ Architecture

### Tech Stack
- **Framework**: Chainlit (async web UI)
- **Agent**: LangGraph + LangChain
- **LLM Providers**: 
  - OpenAI (GPT-4o-mini, GPT-5.1)
  - Ollama (local Mistral 7B)
- **Data Sources**: NOAA API, NWAC API, Powder Poobah
- **Visualizations**: Plotly
- **Deployment**: Python 3.9+, UV package manager

### Key Components
```
snow-assistant/
├── app.py                 # Chainlit UI with streaming
├── agents/
│   └── workflow.py        # LangGraph agent with tool calling
├── models/
│   └── local_llm.py       # Unified LLM wrapper (Ollama/OpenAI)
├── tools/
│   └── basic_tools.py     # Weather & avalanche forecast tools
├── config.py              # LLM provider configuration
└── pyproject.toml         # Dependencies
```

## 🚀 Setup

### Prerequisites
- Python 3.9+
- [UV package manager](https://github.com/astral-sh/uv) (recommended) or pip
- OpenAI API key OR Ollama running locally

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/snow-assistant.git
cd snow-assistant
```

### 2. Install UV (if not installed)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Install Dependencies
```bash
# UV automatically creates venv and installs dependencies
uv sync
```

### 4. Configure Environment
Create a `.env` file in the project root:

```bash
# LLM Provider Selection
LLM_PROVIDER=openai          # Options: "openai" or "ollama"

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL_NAME=gpt-4o-mini  # or gpt-5.1, gpt-4o

# Ollama Configuration (if using local Ollama)
OLLAMA_MODEL_NAME=mistral:7b-instruct-q4_K_M
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Logging
LOG_LEVEL=INFO
```

### 5. Start Ollama (if using local LLM)
```bash
# Install Ollama from https://ollama.ai
ollama serve

# Pull model (in another terminal)
ollama pull mistral:7b-instruct-q4_K_M
```

## 🎮 Usage

### Start the Application
```bash
# Using UV (recommended)
uv run chainlit run app.py -w

# Using pip/venv
chainlit run app.py -w
```

The app will open at `http://localhost:8000`

### Example Queries
- **"Analyze snow forecast for Stevens Pass"** - Comprehensive analysis with charts
- **"What's the avalanche danger?"** - NWAC forecast integration
- **"When is the next powder day?"** - Snowfall timing analysis
- **"Show me the weather forecast"** - Basic NOAA forecast with visualizations

### Chat Features
- **Streaming Responses**: See analysis appear in real-time
- **Interactive Charts**: Hover over Plotly visualizations for details
- **Multi-Turn Conversations**: Ask follow-up questions
- **Expert Context**: Powder Poobah insights included automatically

## 🔧 Configuration

### LLM Provider Selection

**OpenAI (Recommended for Production)**
```python
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL_NAME=gpt-4o-mini  # Fast and cost-effective
```

**Ollama (Local GPU)**
```python
# .env
LLM_PROVIDER=ollama
OLLAMA_MODEL_NAME=mistral:7b-instruct-q4_K_M
```

### Model Parameters
Edit `config.py` to adjust:
- `temperature`: Response creativity (0.0-1.0)
- `max_tokens`: Response length limit
- `num_ctx`: Context window size (Ollama)

## 📊 Data Sources

### NOAA Weather API
- **Endpoint**: `api.weather.gov`
- **Coverage**: Stevens Pass grid point (OTX)
- **Data**: Hourly forecasts, grid data, alerts
- **Refresh**: Real-time API calls

### Northwest Avalanche Center (NWAC)
- **Endpoint**: `nwac.us`
- **Coverage**: Stevens Pass zone
- **Data**: Danger ratings, bottom line, discussion
- **Refresh**: Updated daily

### Powder Poobah
- **Endpoint**: `powderpoobah.com`
- **Coverage**: Pacific Northwest forecasts
- **Data**: Short-term, extended outlook, highlights
- **Refresh**: Web scraping from latest post

## 🐛 Troubleshooting

### Streaming Issues
The app uses thread-safe Future-based streaming. If text doesn't appear:
- Check logs for "Chainlit context not available" (expected, fallback works)
- Content is set as fallback automatically

### Ollama Connection
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Restart Ollama service
ollama serve
```

### OpenAI API Errors
- Verify API key in `.env`
- Check rate limits and quota
- Ensure model name is correct

### No Weather Data
- NOAA API may be temporarily down
- Check network connectivity
- Verify coordinates (47.7462, -121.0859)

## 🏗️ Development

### Project Structure
- **`app.py`**: Chainlit UI, message handling, streaming logic
- **`agents/workflow.py`**: LangGraph state machine, tool execution
- **`models/local_llm.py`**: Unified LLM wrapper with streaming support
- **`tools/basic_tools.py`**: Weather API integrations, plot generation
- **`config.py`**: Environment-based configuration

### Adding New Tools
1. Define tool function in `tools/basic_tools.py`
2. Wrap with `Tool()` and add to `tools` list
3. Update agent prompt to include new capability

### Testing
```bash
# Test NOAA API
uv run python tests/test_noaa_api.py

# Test NWAC integration
uv run python tests/test_nwac_integration.py

# Test tool calling
uv run python tests/test_tool_calling.py
```

## 📝 Architecture Notes

### Streaming Implementation
- **Thread Pool Execution**: `loop.run_in_executor()` for blocking LLM calls
- **Future Tracking**: `run_coroutine_threadsafe()` with explicit synchronization
- **Fallback Handling**: Automatic content setting on streaming failure
- **Context Limitation**: Chainlit context unavailable from thread pool (handled gracefully)

### Agent Design
- **State-Based**: LangGraph manages conversation state
- **Tool Detection**: JSON response detection prevents streaming tool calls
- **Error Recovery**: Multiple fallback layers for robustness
- **Plot Generation**: Async context handling for Chainlit elements

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 🙏 Acknowledgments

- NOAA for weather data API
- Northwest Avalanche Center for safety information
- Powder Poobah for expert snow forecasts
- LangChain/LangGraph for agent framework
- Chainlit for the UI framework