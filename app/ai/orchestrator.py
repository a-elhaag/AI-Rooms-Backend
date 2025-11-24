"""
AI Orchestrator for managing agent decisions and workflow.
"""

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.gemini_client import gemini_client
from app.ai.tools import tool_create_task, tool_web_search


class AIOrchestrator:
    """
    Main orchestrator for AI agent decisions and actions.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    def _get_tool_definitions(self) -> list[dict]:
        """Define available tools for Gemini."""
        return [
            {
                "function_declarations": [
                    {
                        "name": "create_task",
                        "description": "Create a new task in the room when a user asks to do something or assigns a task.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {
                                    "type": "STRING",
                                    "description": "The title or description of the task",
                                },
                                "assignee_id": {
                                    "type": "STRING",
                                    "description": "The user ID to assign the task to (optional)",
                                },
                                "due_date": {
                                    "type": "STRING",
                                    "description": "Due date in ISO format (optional)",
                                },
                            },
                            "required": ["title"],
                        },
                    },
                    {
                        "name": "search_web",
                        "description": "Search the web for information when the user asks a question that requires external knowledge.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "query": {
                                    "type": "STRING",
                                    "description": "The search query",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                ]
            }
        ]

    async def handle_message(
        self, room_id: str, user_id: str, content: str, message_id: str
    ) -> Optional[dict]:
        """
        Main entry point for handling new messages.
        """
        if not gemini_client.is_configured():
            return None

        # 1. Prepare context (history)
        # TODO: Fetch real history from DB
        history = []

        # 2. Call Gemini with Tools
        response = await gemini_client.chat_with_history(
            message=content,
            history=history,
            system_instruction="You are a helpful AI assistant in a group chat. You can create tasks and search the web.",
            tools=self._get_tool_definitions(),
        )

        # 3. Handle Response (Text or Function Call)
        # Note: The SDK response structure depends on the version.
        # We check for function calls in the candidates.

        try:
            candidate = response.candidates[0]
            for part in candidate.content.parts:
                if part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = fc.args

                    # Execute the tool
                    result = None
                    if tool_name == "create_task":
                        # Inject db and room_id
                        result = await tool_create_task(
                            self.db,
                            room_id,
                            title=args.get("title"),
                            assignee_id=args.get("assignee_id"),
                            due_date=args.get("due_date"),
                        )
                        return {
                            "action": "tool_call",
                            "tool": "create_task",
                            "result": result,
                            "response_text": f"✅ I've created the task: {args.get('title')}",
                        }

                    elif tool_name == "search_web":
                        # Execute search
                        search_results = await tool_web_search(args.get("query"))
                        # In a real loop, we would feed this back to the LLM.
                        # For now, just return the result.
                        return {
                            "action": "tool_call",
                            "tool": "search_web",
                            "result": search_results,
                            "response_text": f"Here is what I found: {search_results[0]['snippet']}",
                        }

            # If no function call, return text
            return {"action": "send_message", "content": response.text}

        except Exception as e:
            print(f"Error processing AI response: {e}")
            return None

    async def handle_command(
        self, room_id: str, user_id: str, command: str, args: dict
    ) -> dict:
        """
        Handle explicit AI commands (e.g., /summarize, /translate).

        Args:
            room_id: Room ID
            user_id: User ID
            command: Command name
            args: Command arguments

        Returns:
            dict: Command execution result

        TODO:
            - Parse command
            - Execute appropriate tool
            - Return result
        """
        pass

    async def handle_observer_tick(self, room_id: str) -> None:
        """
        Periodic observer that checks room state and takes proactive actions.

        This runs periodically (e.g., every 5-10 minutes) to:
        - Check if goals are being worked on
        - Suggest tasks if needed
        - Update room KB if there's new information

        Args:
            room_id: Room ID

        TODO:
            - Get room context
            - Analyze recent activity
            - Decide if proactive action is needed
            - Take action if appropriate
        """
        pass

    async def gather_room_context(self, room_id: str) -> dict:
        """
        Gather all relevant context for a room.

        Args:
            room_id: Room ID

        Returns:
            dict: Context including messages, tasks, goals, KB

        TODO:
            - Get recent messages (last 20-50)
            - Get active tasks
            - Get active goals
            - Get room KB
            - Get room members
            - Return structured context
        """
        pass
