"""
AI Orchestrator for managing agent decisions and workflow.
"""

from typing import Any, Optional

from app.ai.gemini_client import gemini_client
from app.ai.tools import (tool_create_task, tool_list_tasks,
                          tool_summarize_messages, tool_translate_text,
                          tool_web_search)
from google.genai import types
from motor.motor_asyncio import AsyncIOMotorDatabase


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

        # 1. Gather room context
        context = await self.gather_room_context(room_id)
        
        # 2. Build conversation history from recent messages
        history = []
        recent_messages = context.get('recent_messages', [])
        for msg in recent_messages[-10:]:  # Last 10 messages
            # Parse "name: content" format
            if ': ' in msg:
                name, text = msg.split(': ', 1)
                role = 'model' if name.lower() in ['ai', 'assistant', 'bot'] else 'user'
                history.append({
                    'role': role,
                    'parts': [text]
                })
        
        # 3. Build enhanced system instruction with context
        system_parts = [
            "You are a helpful AI assistant in a group chat room.",
            f"Room: {context.get('room_name', 'AI Room')}",
        ]
        
        if context.get('goals'):
            goals_text = ", ".join([g['title'] for g in context['goals'][:3]])
            system_parts.append(f"Room goals: {goals_text}")
        
        if context.get('active_tasks'):
            tasks_text = f"{len(context['active_tasks'])} active tasks"
            system_parts.append(f"Current tasks: {tasks_text}")
        
        system_parts.extend([
            "",
            "You can:",
            "- Answer questions and provide information",
            "- Create tasks when users ask to do something or assign work",
            "- Search the web for current information",
            "- Translate text between languages",
            "- Summarize recent conversations",
            "",
            "Be helpful, concise, and proactive. If someone asks you to do something, use your tools to help them."
        ])
        
        system_instruction = "\n".join(system_parts)

        # 4. Create Chat Session with tools
        chat = await gemini_client.create_chat(
            history=history,
            system_instruction=system_instruction,
            tools=self._get_tool_definitions(),
        )

        if not chat:
            return None

        # 5. Send User Message
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
        """
        from app.services.goal_service import GoalService
        from app.services.kb_service import KBService
        from app.services.message_service import MessageService
        from app.services.room_service import RoomService
        from app.services.task_service import TaskService
        
        context = {}
        
        try:
            # Get recent messages
            message_service = MessageService(self.db)
            recent_msgs = await message_service.get_recent_messages_for_context(room_id, limit=20)
            context['recent_messages'] = [
                f"{msg.get('sender_name', 'Unknown')}: {msg.get('content', '')}"
                for msg in recent_msgs
            ]
            
            # Get active tasks
            task_service = TaskService(self.db)
            tasks = await task_service.get_room_tasks(room_id)
            context['active_tasks'] = [
                {
                    'title': task.title,
                    'status': task.status,
                    'assignee': task.assignee_name
                }
                for task in tasks if task.status != 'done'
            ]
            
            # Get goals
            goal_service = GoalService(self.db)
            goals = await goal_service.get_room_goals(room_id)
            context['goals'] = [
                {
                    'title': goal.title,
                    'priority': goal.priority
                }
                for goal in goals
            ]
            
            # Get KnowledgeBase
            kb_service = KBService(self.db)
            kb = await kb_service.get_room_kb(room_id)
            if kb:
                context['knowledge_base'] = {
                    'summary': kb.summary,
                    'key_decisions': kb.key_decisions
                }
            
            # Get room info
            room = await self.db.rooms.find_one({"id": room_id})
            if room:
                context['room_name'] = room.get('name', 'Unknown Room')
                
        except Exception as e:
            print(f"Error gathering context: {e}")
        
        return context
