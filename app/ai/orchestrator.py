"""
AI Orchestrator for managing agent decisions and workflow.
"""

from typing import Any, Optional

from google.genai import types
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.ai.gemini_client import gemini_client
from app.ai.tools import (
    tool_create_task,
    tool_list_tasks,
    tool_summarize_messages,
    tool_translate_text,
    tool_web_search,
)


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
                                    "description": "The user ID to assign the task to (optional, use 'ai' for AI)",
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
                        "name": "list_tasks",
                        "description": "List tasks in the current room.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "status": {
                                    "type": "STRING",
                                    "description": "Filter by status (todo, in_progress, done)",
                                }
                            },
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
                    {
                        "name": "translate_text",
                        "description": "Translate text to a target language.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "text": {
                                    "type": "STRING",
                                    "description": "The text to translate",
                                },
                                "target_language": {
                                    "type": "STRING",
                                    "description": "The target language code (e.g., 'en', 'ar', 'fr')",
                                },
                            },
                            "required": ["text", "target_language"],
                        },
                    },
                    {
                        "name": "summarize_messages",
                        "description": "Summarize the recent conversation in the room.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "last_n": {
                                    "type": "INTEGER",
                                    "description": "Number of messages to summarize (default 20)",
                                }
                            },
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
        # NOTE: Placeholder history - integrate DB fetching in future
        history = []

        # 2. Create Chat Session
        chat = await gemini_client.create_chat(
            history=history,
            system_instruction="You are a helpful AI assistant in a group chat. You can create tasks, search the web, translate text, and summarize conversations.",
            tools=self._get_tool_definitions(),
        )

        if not chat:
            return None

        # 3. Send User Message
        try:
            response = chat.send_message(content)

            # 4. Handle Tool Calls Loop
            # We loop because the model might chain multiple tool calls
            while response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]

                if part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = fc.args

                    print(f"Executing tool: {tool_name} with args: {args}")

                    # Execute the tool
                    result = None
                    if tool_name == "create_task":
                        result = await tool_create_task(
                            self.db,
                            room_id,
                            title=args.get("title"),
                            assignee_id=args.get("assignee_id"),
                            due_date=args.get("due_date"),
                        )
                    elif tool_name == "list_tasks":
                        result = await tool_list_tasks(
                            self.db,
                            room_id,
                            status=args.get("status"),
                        )
                    elif tool_name == "search_web":
                        result = await tool_web_search(args.get("query"))
                    elif tool_name == "translate_text":
                        result = await tool_translate_text(
                            text=args.get("text"),
                            target_language=args.get("target_language"),
                        )
                    elif tool_name == "summarize_messages":
                        result = await tool_summarize_messages(
                            self.db,
                            room_id,
                            last_n=int(args.get("last_n", 20)),
                        )

                    # Send result back to Gemini
                    # The SDK expects a Part with function_response
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_name, response={"result": result}
                        )
                    )
                else:
                    # No function call, just text response
                    break

            # Return final text response
            return {"action": "send_message", "content": response.text}

        except Exception as e:
            print(f"Error processing AI response: {e}")
            return {
                "action": "send_message",
                "content": "Sorry, I encountered an error processing your request.",
            }

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
