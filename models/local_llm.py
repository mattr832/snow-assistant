"""Unified LLM wrapper supporting Ollama (local) and OpenAI (cloud) providers"""

import requests
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from config import (
    LLM_PROVIDER,
    OLLAMA_BASE_URL, OLLAMA_MODEL_NAME, OLLAMA_CONFIG,
    OPENAI_API_KEY, OPENAI_MODEL_NAME, OPENAI_CONFIG
)
import logging

logger = logging.getLogger(__name__)


class UnifiedLLM:
    """
    Unified LLM wrapper that supports both Ollama (local GPU) and OpenAI (cloud API).
    
    Provider is selected via LLM_PROVIDER environment variable:
    - "ollama" → Local models via Ollama (free, private, GPU-accelerated)
    - "openai" → OpenAI API (paid, cloud-based, most capable)
    
    Usage is identical regardless of provider.
    """

    def __init__(self):
        self.provider = LLM_PROVIDER
        self.llm = None
        self._initialize_llm()

    @property
    def model_name(self) -> str:
        """Get the current model name"""
        if self.provider == "ollama":
            return OLLAMA_MODEL_NAME
        elif self.provider == "openai":
            return OPENAI_MODEL_NAME
        return "unknown"

    def _initialize_llm(self):
        """Initialize LLM based on selected provider"""
        
        if self.provider == "ollama":
            self._initialize_ollama()
        elif self.provider == "openai":
            self._initialize_openai()
        else:
            raise ValueError(
                f"Invalid LLM_PROVIDER: {self.provider}. "
                "Must be 'ollama' or 'openai'"
            )

    def _initialize_ollama(self):
        """Initialize Ollama local LLM"""
        try:
            self.llm = OllamaLLM(
                model=OLLAMA_MODEL_NAME,
                base_url=OLLAMA_BASE_URL,
                temperature=OLLAMA_CONFIG["temperature"],
                top_p=OLLAMA_CONFIG["top_p"],
                top_k=OLLAMA_CONFIG["top_k"],
                num_predict=OLLAMA_CONFIG["num_predict"],
                model_kwargs={"num_ctx": OLLAMA_CONFIG["num_ctx"]},
            )
            logger.info(
                f"✓ Initialized Ollama: {OLLAMA_MODEL_NAME} at {OLLAMA_BASE_URL} "
                f"(ctx: {OLLAMA_CONFIG['num_ctx']})"
            )
        except Exception as e:
            logger.error(f"✗ Failed to initialize Ollama: {e}")
            raise

    def _initialize_openai(self):
        """Initialize OpenAI cloud LLM"""
        try:
            if not OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY not set. Add it to .env file or set environment variable."
                )
            
            self.llm = ChatOpenAI(
                model=OPENAI_MODEL_NAME,
                api_key=OPENAI_API_KEY,
                temperature=OPENAI_CONFIG["temperature"],
                max_tokens=OPENAI_CONFIG["max_tokens"],
            )
            logger.info(f"✓ Initialized OpenAI: {OPENAI_MODEL_NAME}")
        except Exception as e:
            logger.error(f"✗ Failed to initialize OpenAI: {e}")
            raise

    def check_connection(self) -> bool:
        """Check if LLM provider is accessible"""
        if self.provider == "ollama":
            return self._check_ollama_connection()
        elif self.provider == "openai":
            return self._check_openai_connection()
        return False

    def _check_ollama_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.ConnectionError:
            logger.error(
                f"✗ Cannot connect to Ollama at {OLLAMA_BASE_URL}. "
                "Make sure Ollama is running: ollama serve"
            )
            return False

    def _check_openai_connection(self) -> bool:
        """Check if OpenAI API is accessible (simple key validation)"""
        try:
            # Try a minimal API call to validate key
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            client.models.list()  # Simple validation call
            return True
        except Exception as e:
            logger.error(f"✗ Cannot connect to OpenAI API: {e}")
            return False

    def generate(self, prompt: str) -> str:
        """Generate text using configured LLM provider"""
        if not self.llm:
            raise RuntimeError("LLM not initialized")
        
        if self.provider == "openai":
            # OpenAI ChatModels expect messages, not raw prompt
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            return response.content
        else:
            # Ollama expects raw prompt
            return self.llm.invoke(prompt)

    def generate_stream(self, prompt: str):
        """Generate text with streaming"""
        if not self.llm:
            raise RuntimeError("LLM not initialized")
        
        if self.provider == "openai":
            # OpenAI streaming with messages
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content=prompt)]
            for chunk in self.llm.stream(messages):
                # ChatOpenAI streams AIMessageChunk objects
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)
        else:
            # Ollama streaming with raw prompt
            for chunk in self.llm.stream(prompt):
                yield chunk

    def get_model_info(self) -> dict:
        """Get information about the current model"""
        if self.provider == "ollama":
            try:
                response = requests.get(
                    f"{OLLAMA_BASE_URL}/api/show",
                    json={"name": OLLAMA_MODEL_NAME},
                    timeout=10
                )
                if response.status_code == 200:
                    return response.json()
                return {"error": f"Status code: {response.status_code}"}
            except Exception as e:
                return {"error": str(e)}
        elif self.provider == "openai":
            return {
                "provider": "openai",
                "model": OPENAI_MODEL_NAME,
                "config": OPENAI_CONFIG,
            }
        return {"error": "Unknown provider"}

    # Backwards compatibility aliases
    def check_ollama_connection(self) -> bool:
        """Deprecated: Use check_connection() instead"""
        return self.check_connection()


# Backwards compatibility alias
LocalGPULLM = UnifiedLLM
