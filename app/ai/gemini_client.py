"""
Google Gemini Client wrapper for AI operations.
Provides centralized access to Gemini API with retry logic and error handling.
"""

import asyncio
import random
from typing import Any, Dict, List, Optional

from app.config import get_settings
from google import genai
from google.genai import types

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds


async def retry_with_backoff(func, *args, **kwargs):
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Async function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(MAX_RETRIES):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            
            # Check for retryable errors (503, overloaded, rate limit)
            is_retryable = any(x in error_str for x in ['503', 'overload', 'rate', 'quota', 'unavailable'])
            
            if not is_retryable or attempt == MAX_RETRIES - 1:
                raise
            
            # Calculate delay with jitter
            delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
            print(f"[GeminiClient] Retry {attempt + 1}/{MAX_RETRIES} after {delay:.1f}s: {e}")
            await asyncio.sleep(delay)
    
    raise last_exception


class GeminiClient:
    """
    Wrapper for Google Gemini API with retry logic and centralized configuration.
    
    This is the single source of truth for Gemini API access in the application.
    All AI modules should use this client instead of creating their own.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GOOGLE_API_KEY
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if client is configured with API key."""
        return bool(self.client)
    
    def get_raw_client(self) -> Optional[genai.Client]:
        """
        Get the raw genai.Client for advanced operations.
        
        Returns:
            genai.Client or None if not configured
        """
        return self.client

    async def generate_response(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash-lite",
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate a simple text response.

        Args:
            prompt: User prompt
            model: Model name (default: gemini-2.5-flash-lite)
            system_instruction: Optional system instruction

        Returns:
            str: Generated text
        """
        if not self.client:
            return "Error: Google API Key not configured."

        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        try:
            response = self.client.models.generate_content(
                model=model, contents=prompt, config=config
            )
            return response.text
        except Exception as e:
            print(f"Gemini API Error: {e}")
            return f"I'm sorry, I'm currently overloaded. Please try again in a moment. (Error: {str(e)})"

    async def search_web(self, query: str) -> str:
        """
        Perform a web search using Gemini Grounding.

        Args:
            query: Search query

        Returns:
            str: AI response based on search results
        """
        if not self.client:
            return "Error: Google API Key not configured."

        try:
            # Use Gemini 2.5 Flash Lite for search grounding
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=query,
                config={"tools": [{"google_search": {}}]},
            )
            return response.text
        except Exception as e:
            print(f"Gemini Search Error: {e}")
            return f"I couldn't search the web right now. (Error: {str(e)})"

    async def create_chat(
        self,
        history: List[Dict[str, str]],
        system_instruction: str = (
            "You are Veya, a friendly, proactive AI teammate in a collaborative workspace. "
            "Be concise, focus on useful answers, and use light humor only when the tone is casual—skip jokes when things are urgent or serious."
        ),
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Create a new chat session.

        Args:
            history: List of dicts with 'role' ('user' or 'model') and 'parts' (text)
            system_instruction: System prompt
            tools: Optional list of tool definitions (JSON schema)

        Returns:
            ChatSession object
        """
        if not self.client:
            return None

        config = {"system_instruction": system_instruction}
        if tools:
            config["tools"] = tools

        try:
            # Convert history to proper Content objects
            formatted_history = []
            for msg in history:
                role = msg.get('role', 'user')
                parts = msg.get('parts', [])
                if isinstance(parts, list) and len(parts) > 0:
                    text = parts[0] if isinstance(parts[0], str) else str(parts[0])
                    formatted_history.append(
                        types.Content(role=role, parts=[types.Part.from_text(text=text)])
                    )
            
            return self.client.chats.create(
                model="gemini-2.5-flash-lite", config=config, history=formatted_history
            )
        except Exception as e:
            print(f"Gemini Chat Error: {e}")
            return None

    async def chat_with_history(
        self,
        message: str,
        history: List[Dict[str, str]],
        system_instruction: str = (
            "You are Veya, a friendly, proactive AI teammate in a collaborative workspace. "
            "Be concise, focus on useful answers, and use light humor only when the tone is casual—skip jokes when things are urgent or serious."
        ),
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Any:
        """
        Chat with conversation history and optional tools.

        Args:
            message: New user message
            history: List of dicts with 'role' ('user' or 'model') and 'parts' (text)
            system_instruction: System prompt
            tools: Optional list of tool definitions (JSON schema)

        Returns:
            Response object (containing text or function calls)
        """
        if not self.client:
            return "Error: Google API Key not configured."

        config = {"system_instruction": system_instruction}
        if tools:
            config["tools"] = tools

        # Convert history to proper Content objects
        formatted_history = []
        for msg in history:
            role = msg.get('role', 'user')
            parts = msg.get('parts', [])
            if isinstance(parts, list) and len(parts) > 0:
                text = parts[0] if isinstance(parts[0], str) else str(parts[0])
                formatted_history.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=text)])
                )

        chat = self.client.chats.create(
            model="gemini-2.5-flash-lite", config=config, history=formatted_history
        )

        response = chat.send_message(message)
        return response


    async def generate_embedding(self, text: str, model: str = "models/text-embedding-004") -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed (will be truncated to 8000 chars)
            model: Embedding model name
            
        Returns:
            List[float]: Embedding vector (768 dimensions) or zeros on failure
        """
        if not self.client:
            print("Error generating embedding: GOOGLE_API_KEY not configured")
            return [0.0] * 768
        
        try:
            result = self.client.models.embed_content(
                model=model,
                contents=text[:8000]  # Limit text length
            )
            return result.embeddings[0].values
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * 768


# Global instance - use this everywhere instead of creating new clients
gemini_client = GeminiClient()
