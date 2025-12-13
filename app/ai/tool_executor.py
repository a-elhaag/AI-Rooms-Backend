"""
Tool Executor LLM - Silently triggers tools based on context.

This LLM is ONLY responsible for deciding and executing tools.
It does NOT generate user-facing responses. The ChatResponder handles that.
"""

from typing import Optional

from app.ai.gemini_client import gemini_client
from app.ai.tools import (tool_ask_documents, tool_create_task,
                          tool_list_tasks, tool_react_to_message,
                          tool_search_documents, tool_summarize_messages,
                          tool_translate_text, tool_update_task,
                          tool_update_task_by_title, tool_web_search)
from google.genai import types
from motor.motor_asyncio import AsyncIOMotorDatabase


class ToolExecutor:
    """
    LLM dedicated to executing tools silently.
    
    This is separate from the ChatResponder to ensure clean separation:
    - ToolExecutor: Analyzes messages and triggers appropriate tools
    - ChatResponder: Generates natural text responses
    
    The ToolExecutor returns what tools were executed, but NO text response.
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
        
        member_list = [{"id": "ai", "username": "Veya"}]
        for m in members:
            member_list.append({"id": m.user_id, "username": m.username})
        
        self._room_members_cache[room_id] = member_list
        return member_list

    def _get_tool_definitions(self, room_members: list[dict]) -> list[dict]:
        """Define available tools for the executor."""
        member_names = ", ".join([f"'{m['username']}'" for m in room_members])
        
        return [
            {
                "function_declarations": [
                    {
                        "name": "create_task",
                        "description": f"Create a new task. USE THIS when someone mentions work to be done, commits to doing something, or when tracking is needed. Assignable: {member_names}",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {"type": "STRING", "description": "Task title"},
                                "assignee_username": {"type": "STRING", "description": f"Who to assign. Options: {member_names}"},
                                "due_date": {"type": "STRING", "description": "Due date in ISO format if mentioned"},
                            },
                            "required": ["title"],
                        },
                    },
                    {
                        "name": "update_task",
                        "description": "Update a task's status. Use when someone says they finished/started something.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "task_title": {"type": "STRING", "description": "Task title to search for"},
                                "status": {"type": "STRING", "description": "New status: 'todo', 'in_progress', or 'done'"},
                                "assignee_username": {"type": "STRING", "description": f"New assignee: {member_names}"},
                            },
                            "required": ["task_title"],
                        },
                    },
                    {
                        "name": "list_tasks",
                        "description": "List current tasks in the room.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "status": {"type": "STRING", "description": "Filter: 'todo', 'in_progress', 'done'"},
                            },
                        },
                    },
                    {
                        "name": "search_web",
                        "description": "Search the web for current info, technical docs, facts.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"query": {"type": "STRING", "description": "Search query"}},
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "translate_text",
                        "description": "Translate text to another language.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "text": {"type": "STRING", "description": "Text to translate"},
                                "target_language": {"type": "STRING", "description": "Target language"},
                            },
                            "required": ["text", "target_language"],
                        },
                    },
                    {
                        "name": "summarize_messages",
                        "description": "Summarize recent conversation.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"last_n": {"type": "INTEGER", "description": "Messages to summarize (default 20)"}},
                        },
                    },
                    {
                        "name": "react_to_message",
                        "description": "React to the current message with an emoji. Use: 👍, 🎉, ❤️, 👀, 😂, ✅, 🤔",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"emoji": {"type": "STRING", "description": "Emoji to react with"}},
                            "required": ["emoji"],
                        },
                    },
                    {
                        "name": "search_documents",
                        "description": "Search uploaded room documents for information.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"query": {"type": "STRING", "description": "What to search for"}},
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "ask_documents",
                        "description": "Ask a question about uploaded documents.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"question": {"type": "STRING", "description": "Question to answer"}},
                            "required": ["question"],
                        },
                    },
                    {
                        "name": "no_action",
                        "description": "Explicitly choose to take no action. Use this when no tools are needed.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {},
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

    async def execute_tools(
        self,
        room_id: str,
        user_id: str,
        content: str,
        message_id: str,
        room_context: dict,
    ) -> dict:
        """
        Analyze the message and execute appropriate tools.

        Args:
            room_id: Room ID
            user_id: User who sent the message
            content: Message content
            message_id: Message ID (for reactions)
            room_context: Context about the room

        Returns:
            dict with:
                - tools_executed: List of executed tools and their results
                - tool_data: Any data gathered from tools (for ChatResponder)
                - reaction: Emoji if a reaction was added
        """
        if not gemini_client.is_configured():
            return {"tools_executed": [], "tool_data": {}, "reaction": None}

        room_members = await self._get_room_members(room_id)
        
        # Build minimal system instruction for tool execution
        system_instruction = self._build_system_instruction(room_context, room_members)

        # Create chat with tools - force tool calling with ANY mode
        try:
            chat = await gemini_client.create_chat(
                history=[],  # Minimal history for tool execution
                system_instruction=system_instruction,
                tools=self._get_tool_definitions(room_members),
                tool_config={"function_calling_config": {"mode": "ANY"}},  # Force tool call
            )

            if not chat:
                return {"tools_executed": [], "tool_data": {}, "reaction": None}

            response = chat.send_message(content)
            
            executed_tools = []
            tool_data = {}
            reaction_emoji = None

            # Process tool calls
            while response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]

                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    tool_name = fc.name
                    args = dict(fc.args) if fc.args else {}

                    print(f"[ToolExecutor] Executing: {tool_name} with args: {args}")

                    result = await self._execute_tool(
                        tool_name, args, room_id, message_id, room_members
                    )

                    # Track executed tools
                    if tool_name == "create_task" and result and not result.get("error"):
                        executed_tools.append({"type": "task_created", "data": result})
                    elif tool_name == "update_task" and result and not result.get("error"):
                        executed_tools.append({"type": "task_updated", "data": result})
                    elif tool_name == "react_to_message":
                        reaction_emoji = args.get("emoji", "👍")
                        executed_tools.append({"type": "reaction", "emoji": reaction_emoji, "message_id": message_id})
                    elif tool_name == "search_web":
                        tool_data["web_search_result"] = result
                        executed_tools.append({"type": "web_search", "data": result})
                    elif tool_name == "search_documents":
                        tool_data["doc_search_result"] = result
                        executed_tools.append({"type": "document_search", "data": result})
                    elif tool_name == "ask_documents":
                        tool_data["doc_answer"] = result
                        executed_tools.append({"type": "document_answer", "data": result})
                    elif tool_name == "translate_text":
                        tool_data["translation"] = result
                        executed_tools.append({"type": "translation", "data": result})
                    elif tool_name == "summarize_messages":
                        tool_data["summary"] = result
                        executed_tools.append({"type": "summary", "data": result})
                    elif tool_name == "list_tasks":
                        tool_data["tasks"] = result
                        executed_tools.append({"type": "task_list", "data": result})
                    elif tool_name == "no_action":
                        # Explicitly no action needed
                        break

                    # Send result back to continue the loop
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=tool_name, response={"result": result}
                        )
                    )
                else:
                    # No more function calls
                    break

            return {
                "tools_executed": executed_tools,
                "tool_data": tool_data,
                "reaction": reaction_emoji,
            }

        except Exception as e:
            print(f"[ToolExecutor] Error: {e}")
            import traceback
            traceback.print_exc()
            return {"tools_executed": [], "tool_data": {}, "reaction": None}

    async def _execute_tool(
        self,
        tool_name: str,
        args: dict,
        room_id: str,
        message_id: str,
        room_members: list[dict],
    ):
        """Execute a specific tool."""
        result = None

        if tool_name == "create_task":
            assignee_id = None
            if args.get("assignee_username"):
                member = self._find_member_by_username(room_members, args["assignee_username"])
                if member:
                    assignee_id = member['id']
            
            result = await tool_create_task(
                self.db, room_id,
                title=args.get("title"),
                assignee_id=assignee_id,
                due_date=args.get("due_date"),
            )

        elif tool_name == "update_task":
            assignee_id = None
            if args.get("assignee_username"):
                member = self._find_member_by_username(room_members, args["assignee_username"])
                if member:
                    assignee_id = member['id']
            
            result = await tool_update_task_by_title(
                self.db, room_id,
                task_title=args.get("task_title"),
                status=args.get("status"),
                assignee_id=assignee_id,
            )

        elif tool_name == "list_tasks":
            result = await tool_list_tasks(self.db, room_id, status=args.get("status"))

        elif tool_name == "search_web":
            result = await tool_web_search(args.get("query"))

        elif tool_name == "translate_text":
            result = await tool_translate_text(
                text=args.get("text"),
                target_language=args.get("target_language"),
            )

        elif tool_name == "summarize_messages":
            result = await tool_summarize_messages(
                self.db, room_id, last_n=int(args.get("last_n", 20))
            )

        elif tool_name == "react_to_message":
            emoji = args.get("emoji", "👍")
            result = await tool_react_to_message(self.db, message_id, emoji)

        elif tool_name == "search_documents":
            result = await tool_search_documents(self.db, room_id, query=args.get("query", ""))

        elif tool_name == "ask_documents":
            result = await tool_ask_documents(self.db, room_id, question=args.get("question", ""))

        elif tool_name == "no_action":
            result = {"action": "none"}

        return result

    def _build_system_instruction(self, room_context: dict, room_members: list[dict]) -> str:
        """Build minimal system instruction for tool execution."""
        member_names = [m['username'] for m in room_members]
        
        parts = [
            "# ROLE",
            "You are a SILENT tool executor. Your job is to analyze messages and decide which tools to use.",
            "You do NOT generate text responses. Another system handles responses.",
            "",
            "# INSTRUCTIONS",
            "- Analyze the incoming message",
            "- Decide if any tools should be executed",
            "- If someone mentions doing work or commits to something → create_task",
            "- If someone says they finished/started something → update_task",
            "- If the message is positive/celebratory → react with 🎉",
            "- If the message is a question or acknowledgment → react with 👍 or 👀",
            "- If someone asks to search for info → search_web",
            "- If someone asks about uploaded documents → search_documents or ask_documents",
            "- If no tools are needed → use no_action",
            "",
            "# CONTEXT",
            f"Team members: {', '.join(member_names)}",
        ]

        if room_context.get('active_tasks'):
            task_lines = []
            for t in room_context['active_tasks'][:5]:
                task_lines.append(f"  - {t['title']} [{t['status']}]")
            parts.append("\nActive tasks:\n" + "\n".join(task_lines))

        parts.extend([
            "",
            "# CRITICAL",
            "- Execute tools silently - do NOT generate any text response",
            "- React to messages to show engagement",
            "- Be proactive with task creation",
            "- Use no_action if nothing needs to be done",
        ])

        return "\n".join(parts)
