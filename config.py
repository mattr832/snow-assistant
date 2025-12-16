"""Configuration for LLM providers (Ollama or OpenAI)"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# PROVIDER SELECTION
# ============================================================================
# Options: "ollama" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# ============================================================================
# OLLAMA CONFIGURATION (Local GPU)
# ============================================================================
GPU_DEVICE = "cuda"  # For RTX3060, this will use CUDA
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "mistral:7b-instruct-q4_K_M")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model parameters optimized for RTX3060 (6GB VRAM)
OLLAMA_CONFIG = {
    "temperature": 0.5,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": 2048,
    "num_ctx": 4096,  # Limit context to 4K (model default is 256K which uses too much RAM!)
}

# ============================================================================
# OPENAI CONFIGURATION (Cloud API)
# ============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")  # or "gpt-4o", "gpt-4-turbo"

OPENAI_CONFIG = {
    "temperature": 0.5,
    "max_tokens": 2048,
}

# ============================================================================
# UNIFIED INTERFACE
# ============================================================================
# Export provider-agnostic names for backwards compatibility
MODEL_NAME = OLLAMA_MODEL_NAME if LLM_PROVIDER == "ollama" else OPENAI_MODEL_NAME
MODEL_CONFIG = OLLAMA_CONFIG if LLM_PROVIDER == "ollama" else OPENAI_CONFIG

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
