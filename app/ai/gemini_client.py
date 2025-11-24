"""
Google Gemini Client wrapper for AI operations.
"""

from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.config import get_settings


class GeminiClient:
    """Wrapper for Google Gemini API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GOOGLE_API_KEY
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if client is configured with API key."""
        return bool(self.client)

    async def generate_response(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Generate a simple text response.

        Args:
            prompt: User prompt
            model: Model name (default: gemini-2.0-flash-exp)
            system_instruction: Optional system instruction

        Returns:
            str: Generated text
        """
        if not self.client:
            return "Error: Google API Key not configured."

        config = {}
        if system_instruction:
            config["system_instruction"] = system_instruction

        response = self.client.models.generate_content(
            model=model, contents=prompt, config=config
        )
        return response.text

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

        # Use Gemini 2.0 Flash or Pro for search grounding
        response = self.client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=query,
            config={"tools": [{"google_search": {}}]},
        )

        # Extract text from response
        # Note: The actual search results (metadata) are in response.candidates[0].grounding_metadata
        # But for now we just return the synthesized text.
        return response.text

    async def chat_with_history(
        self,
        message: str,
        history: List[Dict[str, str]],
        system_instruction: str = "You are a helpful AI assistant in a group chat.",
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

        chat = self.client.chats.create(
            model="gemini-2.0-flash-exp", config=config, history=history
        )

        response = chat.send_message(message)
        return response


# Global instance
gemini_client = GeminiClient()
