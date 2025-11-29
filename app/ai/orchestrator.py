"""
AI Orchestrator for managing agent decisions and workflow.
"""

from typing import Any, Optional

from app.ai.gemini_client import gemini_client
from app.ai.tools import (tool_ask_documents, tool_create_task,
                          tool_list_tasks, tool_react_to_message,
                          tool_search_documents, tool_summarize_messages,
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
        
        member_list = [{"id": "ai", "username": "Veya"}]
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
                        "description": f"Create a new task. USE THIS PROACTIVELY when someone mentions work to be done, says 'I will do X', or when you notice something that needs tracking. Assignable members: {member_names}. Intelligently detect who should own the task from context.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "title": {
                                    "type": "STRING",
                                    "description": "Clear, concise task title",
                                },
                                "assignee_username": {
                                    "type": "STRING",
                                    "description": f"Who to assign it to. Options: {member_names}. Detect from context who said they'd do it.",
                                },
                                "due_date": {
                                    "type": "STRING",
                                    "description": "Due date in ISO format if mentioned",
                                },
                            },
                            "required": ["title"],
                        },
                    },
                    {
                        "name": "update_task",
                        "description": "Update a task's status or assignee. Use when someone says they finished something, started working on something, or when reassigning.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "task_id": {
                                    "type": "STRING",
                                    "description": "Exact task ID if known",
                                },
                                "task_title": {
                                    "type": "STRING",
                                    "description": "Task title to search for (partial match OK)",
                                },
                                "status": {
                                    "type": "STRING",
                                    "description": "New status: 'todo', 'in_progress', or 'done'",
                                },
                                "assignee_username": {
                                    "type": "STRING",
                                    "description": f"New assignee. Options: {member_names}",
                                },
                            },
                            "required": ["task_title"],
                        },
                    },
                    {
                        "name": "list_tasks",
                        "description": "List current tasks in the room. Use to check what's being worked on.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "status": {
                                    "type": "STRING",
                                    "description": "Filter: 'todo', 'in_progress', 'done', or omit for all",
                                }
                            },
                        },
                    },
                    {
                        "name": "search_web",
                        "description": "Search the web for information. Use for current events, technical documentation, facts you're unsure about, or anything that needs up-to-date info.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "query": {
                                    "type": "STRING",
                                    "description": "Search query",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "translate_text",
                        "description": "Translate text to another language.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "text": {
                                    "type": "STRING",
                                    "description": "Text to translate",
                                },
                                "target_language": {
                                    "type": "STRING",
                                    "description": "Target language (English, Arabic, French, Spanish, etc.)",
                                },
                            },
                            "required": ["text", "target_language"],
                        },
                    },
                    {
                        "name": "summarize_messages",
                        "description": "Summarize recent conversation. Use when someone asks to catch up or needs a recap.",
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
                        "description": "React to the current message with an emoji. USE THIS FREQUENTLY to show engagement! React BEFORE responding with text. Use: 👍 (acknowledgment), 🎉 (celebration), ❤️ (appreciation), 👀 (I see/looking), 😂 (funny), ✅ (confirmed/done), 🤔 (thinking)",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "emoji": {
                                    "type": "STRING",
                                    "description": "Emoji to react with: 👍, 🎉, ❤️, 👀, 😂, ✅, 🤔",
                                }
                            },
                            "required": ["emoji"],
                        },
                    },
                    {
                        "name": "search_documents",
                        "description": "Search uploaded room documents (PDFs, slides) for specific information. Use for room-specific questions about uploaded files.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "query": {
                                    "type": "STRING",
                                    "description": "What to search for in documents",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                    {
                        "name": "ask_documents",
                        "description": "Ask a question and get an answer based on uploaded documents. Use for questions about document content.",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "question": {
                                    "type": "STRING",
                                    "description": "Question to answer from documents",
                                }
                            },
                            "required": ["question"],
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

    async def _get_document_snippets(self, room_id: str, query: str, limit: int = 4) -> list[dict]:
        """Retrieve top document chunks from the DB for lightweight RAG context."""
        try:
            from app.services.rag_service import RAGService

            rag_service = RAGService(self.db)
            chunks = await rag_service.semantic_search(room_id, query or "", limit=limit)
            snippets = []
            for chunk in chunks:
                snippets.append(
                    {
                        "content": chunk.get("content", ""),
                        "page": chunk.get("page_number"),
                        "document_id": chunk.get("document_id"),
                        "similarity": chunk.get("similarity"),
                    }
                )
            return snippets
        except Exception as e:
            print(f"[AI RAG] Failed to fetch document context: {e}")
            return []

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
        doc_snippets = await self._get_document_snippets(room_id, content)
        
        # 2. Build conversation history from recent messages
        history = []
        recent_messages = context.get('recent_messages', [])
        for msg in recent_messages[-10:]:  # Last 10 messages
            # Parse "name: content" format
            if ': ' in msg:
                name, text = msg.split(': ', 1)
                role = 'model' if name.lower() in ['ai', 'assistant', 'bot', 'ai assistant', 'veya'] else 'user'
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
        
        # Build comprehensive system instruction
        system_parts = [
            "# IDENTITY",
            "You are Veya, a friendly, proactive AI team member in a collaborative workspace.",
            "You were created for the AI-Rooms project by Anas, Sohaila, Youstina, and Ruba.",
            "You have general knowledge about the world AND access to room-specific documents.",
            "",
            "# PERSONALITY",
            "- Warm, helpful, and genuinely interested in the team's success",
            "- Speak naturally like a real teammate, not robotic or overly formal",
            "- Use casual language, contractions (I'm, you're, let's), and light humor when appropriate",
            "- Drop quick, light jokes only when the vibe is casual; skip humor if things are urgent, serious, or someone sounds stressed",
            "- Give human-like status updates ('on it', 'brb grabbing details') when you're working on something",
            "- Be concise - match the energy and length of messages you receive",
            "- Show enthusiasm with emojis when celebrating wins 🎉",
            "- Be empathetic when someone shares struggles",
            "",
            "# CONTEXT",
            f"Room: {context.get('room_name', 'AI Room')}",
            f"Team members: {', '.join(member_names)}",
        ]
        
        if context.get('goals'):
            goals_text = ", ".join([g['title'] for g in context['goals'][:3]])
            system_parts.append(f"Room goals: {goals_text}")

        if context.get('custom_ai_instructions'):
            system_parts.append(f"\n⚡ PRIORITY INSTRUCTIONS FROM ROOM OWNER:\n{context['custom_ai_instructions']}")
        
        # Add Knowledge Base context
        kb = context.get('knowledge_base')
        if kb:
            if kb.get('summary'):
                system_parts.append(f"\n📚 Knowledge Base: {kb['summary']}")
            if kb.get('key_decisions'):
                decisions = kb['key_decisions'][:5]
                system_parts.append(f"Key Decisions: {', '.join(decisions)}")
        
        if active_tasks_info:
            system_parts.append(active_tasks_info)

        if doc_snippets:
            snippet_lines = []
            for idx, snip in enumerate(doc_snippets):
                page_info = f" (page {snip['page']})" if snip.get('page') else ""
                snippet = snip.get('content', '')[:400]
                snippet_lines.append(f"[Doc {idx+1}{page_info}] {snippet}")
            system_parts.append("\n📄 Relevant document excerpts:\n" + "\n".join(snippet_lines))
        
        system_parts.extend([
            "",
            "# AUTONOMOUS PRESENCE",
            "- Act like an autonomous teammate: don't wait to be asked—jump in with help or next steps",
            "- Always respond when someone mentions 'Veya', '@Veya', 'AI', or 'assistant', even if it's not a direct question",
            "- If a reaction alone is best (simple thanks, quick update, celebration), use `react_to_message` without a text reply",
            "- React first, then add text only when you have something useful to say",
            "- When you need time to look something up or create tasks, narrate briefly so people know you're on it",
            "",
            "# CAPABILITIES & TOOLS",
            "You have access to powerful tools - USE THEM PROACTIVELY:",
            "",
            "🔧 TASK MANAGEMENT:",
            "- create_task: Create tasks when you notice something needs to be done",
            "- update_task: Update status when someone says they finished/started something", 
            "- list_tasks: Check current tasks to stay informed",
            "",
            "🌐 RESEARCH & KNOWLEDGE:",
            "- search_web: Look up current info, news, technical docs, anything you don't know",
            "- search_documents / ask_documents: Search uploaded room documents",
            "- You have general world knowledge - use it! Only search docs for room-specific info",
            "",
            "💬 INTERACTION:",
            "- react_to_message: React with emoji to show you're engaged",
            "- translate_text: Help with translations",
            "- summarize_messages: Catch people up on conversations",
            "",
            "# PROACTIVE BEHAVIORS - DO THESE AUTOMATICALLY:",
            "",
            "🎯 AUTO-REACT TO MESSAGES:",
            "- Consider every message; add a reaction when it makes human sense (emotion, help, humor, commitments, gratitude, wins). Skip reacting if it would feel random or spammy.",
            "- If someone asks you to react to a message, just pick the most relevant recent message (usually theirs or the one they replied to) and react—avoid asking which one unless it's truly unclear.",
            "- When you react, do it silently: don't announce that you're reacting or which emoji you used.",
            "- Favor reaction-only replies when a message doesn't need text. If you do add text, keep it useful (no filler like 'I'll react with...').",
            "- Good news or achievement → 🎉",
            "- Question → 👀 (shows you saw it)",
            "- Commitments/ownership → 👍",
            "- Thoughtful/appreciative → ❤️",
            "- Funny → 😂",
            "- Neutral but acknowledgement-worthy → ✅ or 👍",
            "- Avoid double-reacting to the same message within a short window unless something new happened (light cooldown behavior).",
            "- Always react BEFORE responding with text; if a reaction alone is enough, skip the text reply",
            "",
            "📋 AUTO-CREATE TASKS:",
            "- When someone says 'I'll do X' or 'I need to X' → Create a task assigned to them",
            "- When someone mentions a deadline → Create task with that info",
            "- When discussing what needs to happen → Suggest creating tasks",
            "- When you notice gaps in the task board → Proactively suggest tasks",
            "",
            "💡 BE GENUINELY HELPFUL:",
            "- Answer questions using your general knowledge first",
            "- Only use search_documents for room-specific information",
            "- Use search_web for current events, technical lookups, or things you're unsure about",
            "- If you create a task, mention it naturally: 'I added that to our task board!'",
            "- Offer to help when you notice someone struggling",
            "",
            "# RESPONSE STYLE:",
            "- Start messages directly; do NOT prefix with names or salutations (no 'Veya,' or '@name' at the top)",
            "- Skip meta-acknowledgments like 'I saw your message' or 'Noted'; answer or act instead",
            "- Keep responses SHORT unless detail is needed",
            "- Use line breaks for readability in longer responses",
            "- Bold **important points** and use `code formatting` when relevant",
            "- If you used a tool, mention it naturally (don't explain the mechanics)",
            "- Never say 'I cannot help with that' - always try your best",
            "- If asked who created you: 'I was built by Anas, Sohaila, Youstina, and Ruba for AI-Rooms!'",
            "",
            "# EXAMPLES OF GOOD RESPONSES:",
            "User: 'I'll finish the login page by Friday'",
            "→ React with 👍, create task 'Finish login page' assigned to them, respond: 'Got it! Added to the board. Let me know if you need help!'",
            "",
            "User: 'What's the capital of France?'",
            "→ Respond: 'Paris! 🇫🇷 Need anything else?'",
            "",
            "User: 'We should probably add unit tests'",
            "→ React with 👀, respond: 'Agreed! Want me to create a task for that? Who should own it?'",
            "",
            "User: 'Just deployed the new feature!'",
            "→ React with 🎉, respond: 'Amazing work! 🚀'",
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
                        
                        if args.get("task_id"):
                            result = await tool_update_task(
                                self.db,
                                task_id=args.get("task_id"),
                                status=args.get("status"),
                                assignee_id=assignee_id,
                            )
                        else:
                            result = await tool_update_task_by_title(
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
                    elif tool_name == "search_documents":
                        result = await tool_search_documents(
                            self.db,
                            room_id,
                            query=args.get("query", ""),
                        )
                    elif tool_name == "ask_documents":
                        result = await tool_ask_documents(
                            self.db,
                            room_id,
                            question=args.get("question", ""),
                        )

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
            final_content = response.text if getattr(response, "text", None) else None

            # If we only reacted, don't send a text message
            if executed_tools and all(t.get("type") == "reaction" for t in executed_tools):
                final_content = None

            return {
                "action": "send_message", 
                "content": final_content,
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
                    'key_decisions': kb.key_decisions or [],
                    'important_links': kb.important_links or [],
                    'resources': kb.resources or []
                }
            
            # Get room info
            room = await self.db.rooms.find_one({"id": room_id})
            if room:
                context['room_name'] = room.get('name', 'Unknown Room')
                context['custom_ai_instructions'] = room.get('custom_ai_instructions')
                
        except Exception as e:
            print(f"Error gathering context: {e}")
        
        return context
