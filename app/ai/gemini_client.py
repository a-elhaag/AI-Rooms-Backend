"""
Google Gemini Client wrapper for AI operations.
"""

from typing import Any, Dict, List, Optional

from app.config import get_settings
from google import genai
from google.genai import types


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
        system_instruction: str = "You are Veya, a helpful AI assistant in a group chat.",
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
        system_instruction: str = "You are Veya, a helpful AI assistant in a group chat.",
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


# Global instance
gemini_client = GeminiClient()
