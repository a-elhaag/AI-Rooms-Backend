"""
AI Orchestrator for managing agent decisions and workflow.
"""

from typing import Any, Optional

from app.ai.gemini_client import gemini_client
from app.ai.tools import (tool_create_task, tool_list_tasks,
                          tool_react_to_message, tool_summarize_messages,
                          tool_translate_text, tool_update_task,
                          tool_web_search)
from google.genai import types
from motor.motor_asyncio import AsyncIOMotorDatabase


class AIOrchestrator:
    """
    Main orchestrator for AI agent decisions and actions.
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._room_members_cache = {}

    async def _get_room_members(self, room_id: str) -> list[dict]:
        """Get room members for smart assignment."""
        if room_id in self._room_members_cache:
            return self._room_members_cache[room_id]
        
        from app.services.room_service import RoomService
        room_service = RoomService(self.db)
        members = await room_service.get_room_members(room_id)
        
        member_list = [{"id": "ai", "username": "AI Assistant"}]
        for m in members:
            member_list.append({"id": m.user_id, "username": m.username})
        
        self._room_members_cache[room_id] = member_list
        return member_list

    def _get_tool_definitions(self, room_members: list[dict]) -> list[dict]:
        """Define available tools for Gemini with dynamic member info."""
        member_names = ", ".join([f"'{m['username']}'" for m in room_members])
        
        return [
            {
                "function_declarations": [
                    {
                        "name": "create_task",
                        "description": f"Create a new task in the room. You can assign it to: {member_names}. Detect who should own the task based on context.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {
                                    "type": "STRING",
                                    "description": "The title or description of the task",
                                },
                                "assignee_username": {
                                    "type": "STRING",
                                    "description": f"Username to assign to. Options: {member_names}. Leave empty if unclear.",
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
                        "name": "update_task",
                        "description": "Update an existing task's status or assignee.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "task_title": {
                                    "type": "STRING",
                                    "description": "The title of the task to update (partial match)",
                                },
                                "status": {
                                    "type": "STRING",
                                    "description": "New status: 'todo', 'in_progress', or 'done'",
                                },
                                "assignee_username": {
                                    "type": "STRING",
                                    "description": f"New assignee username. Options: {member_names}",
                                },
                            },
                            "required": ["task_title"],
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
                        "description": "Search the web for current information when the user asks a question that requires external knowledge.",
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
                                    "description": "The target language (e.g., 'English', 'Arabic', 'French', 'Spanish')",
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
                    {
                        "name": "react_to_message",
                        "description": "React to a message with an emoji. Use when you want to acknowledge or show emotion about a message.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "emoji": {
                                    "type": "STRING",
                                    "description": "The emoji to react with (👍, 🎉, ❤️, 👀, 🤔, ✅)",
                                }
                            },
                            "required": ["emoji"],
                        },
                    },
                ]
            }
        ]

    def _find_member_by_username(self, members: list[dict], username: str) -> Optional[dict]:
        """Find a member by username (case-insensitive partial match)."""
        if not username:
            return None
        username_lower = username.lower()
        for member in members:
            if username_lower in member['username'].lower():
                return member
        return None

    async def handle_message(
        self, room_id: str, user_id: str, content: str, message_id: str,
        reply_to_content: Optional[str] = None
    ) -> Optional[dict]:
        """
        Main entry point for handling new messages.
        """
        if not gemini_client.is_configured():
            return None

        # 1. Gather room context and members
        context = await self.gather_room_context(room_id)
        room_members = await self._get_room_members(room_id)
        
        # 2. Build conversation history from recent messages
        history = []
        recent_messages = context.get('recent_messages', [])
        for msg in recent_messages[-10:]:  # Last 10 messages
            # Parse "name: content" format
            if ': ' in msg:
                name, text = msg.split(': ', 1)
                role = 'model' if name.lower() in ['ai', 'assistant', 'bot', 'ai assistant'] else 'user'
                history.append({
                    'role': role,
                    'parts': [text]
                })
        
        # 3. Build enhanced system instruction with context
        member_names = [m['username'] for m in room_members]
        active_tasks_info = ""
        if context.get('active_tasks'):
            task_lines = []
            for t in context['active_tasks'][:5]:
                assignee = f" (assigned to {t['assignee']})" if t.get('assignee') else ""
                task_lines.append(f"  - {t['title']}{assignee} [{t['status']}]")
            active_tasks_info = "\nActive tasks:\n" + "\n".join(task_lines)
        
        system_parts = [
            "You are a smart, helpful AI assistant in a group chat room. You are proactive and can take actions.",
            f"\nRoom: {context.get('room_name', 'AI Room')}",
            f"Room members: {', '.join(member_names)}",
        ]
        
        if context.get('goals'):
            goals_text = ", ".join([g['title'] for g in context['goals'][:3]])
            system_parts.append(f"Room goals: {goals_text}")
        
        if active_tasks_info:
            system_parts.append(active_tasks_info)
        
        system_parts.extend([
            "",
            "CAPABILITIES:",
            "- Create tasks and intelligently assign them based on context",
            "- Update task status and reassign tasks",
            "- Search the web for current information",
            "- Translate text between languages",
            "- Summarize conversations",
            "- React to messages with emoji",
            "",
            "BEHAVIOR:",
            "- Be concise and helpful",
            "- When creating tasks, try to detect the best assignee from context",
            "- If someone says 'I will do X' or 'assign to me', assign to them",
            "- If a task is technical/coding, consider assigning to the person who seems technical",
            "- When asked to do something, use your tools proactively",
            "- React with emoji when appropriate (👍 for acknowledgment, 🎉 for celebration, etc.)",
            "- Always respond naturally after using tools",
        ])
        
        system_instruction = "\n".join(system_parts)

        # 4. Create Chat Session with tools
        chat = await gemini_client.create_chat(
            history=history,
            system_instruction=system_instruction,
            tools=self._get_tool_definitions(room_members),
        )

        if not chat:
            return None

        # 5. Build the user message with reply context
        user_message = content
        if reply_to_content:
            user_message = f'[Replying to: "{reply_to_content}"]\n\n{content}'

        # 6. Send User Message
        try:
            response = chat.send_message(user_message)
            
            executed_tools = []
            reaction_emoji = None

            # 7. Handle Tool Calls Loop
            while response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]

                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = dict(fc.args) if fc.args else {}

                    print(f"[AI TOOL] Executing: {tool_name} with args: {args}")

                    # Execute the tool
                    result = None
                    if tool_name == "create_task":
                        # Resolve username to ID
                        assignee_id = None
                        if args.get("assignee_username"):
                            member = self._find_member_by_username(room_members, args["assignee_username"])
                            if member:
                                assignee_id = member['id']
                        
                        result = await tool_create_task(
                            self.db,
                            room_id,
                            title=args.get("title"),
                            assignee_id=assignee_id,
                            due_date=args.get("due_date"),
                        )
                        executed_tools.append({"type": "task_created", "data": result})
                        
                    elif tool_name == "update_task":
                        # Find task by title and update
                        assignee_id = None
                        if args.get("assignee_username"):
                            member = self._find_member_by_username(room_members, args["assignee_username"])
                            if member:
                                assignee_id = member['id']
                        
                        result = await tool_update_task(
                            self.db,
                            room_id,
                            task_title=args.get("task_title"),
                            status=args.get("status"),
                            assignee_id=assignee_id,
                        )
                        if result and not result.get("error"):
                            executed_tools.append({"type": "task_updated", "data": result})
                            
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
                    elif tool_name == "react_to_message":
                        reaction_emoji = args.get("emoji", "👍")
                        result = await tool_react_to_message(
                            self.db,
                            message_id,
                            reaction_emoji,
                        )
                        if result:
                            executed_tools.append({"type": "reaction", "emoji": reaction_emoji, "message_id": message_id})

                    # Send result back to Gemini
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_name, response={"result": result}
                        )
                    )
                else:
                    # No function call, just text response
                    break

            # Return final text response with tool execution info
            return {
                "action": "send_message", 
                "content": response.text,
                "tools_executed": executed_tools,
                "reaction": reaction_emoji
            }

        except Exception as e:
            print(f"Error processing AI response: {e}")
            import traceback
            traceback.print_exc()
            return {
                "action": "send_message",
                "content": "I encountered an issue processing that. Could you rephrase?",
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
            
            # Get KB
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
