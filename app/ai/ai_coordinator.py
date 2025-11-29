"""
AI Coordinator - Orchestrates the separated LLM architecture.

This is the main entry point for AI processing. It coordinates:
1. ToolExecutor - Silently triggers tools based on message analysis
2. ChatResponder - Generates user-facing text responses

The separation ensures:
- Tools are executed efficiently without response generation overhead
- Responses are natural and focused purely on conversation
- Clear separation of concerns for better maintainability
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase


class AICoordinator:
    """
    Main coordinator for the AI system.
    
    Architecture:
    ┌─────────────────┐
    │   User Message  │
    └────────┬────────┘
             │
    ┌────────▼────────┐
    │  AICoordinator  │
    └────────┬────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
    ┌──────────┐  ┌──────────────┐
    │  Tool    │  │    Chat      │
    │ Executor │  │  Responder   │
    │ (silent) │  │ (text only)  │
    └────┬─────┘  └──────┬───────┘
         │               │
         │   ┌───────┐   │
         └──►│Result │◄──┘
             └───────┘
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._context_cache = {}

    async def _get_room_members(self, room_id: str) -> list[dict]:
        """Get room members."""
        from app.services.room_service import RoomService
        room_service = RoomService(self.db)
        members = await room_service.get_room_members(room_id)
        
        member_list = [{"id": "ai", "username": "Veya"}]
        for m in members:
            member_list.append({"id": m.user_id, "username": m.username})
        
        return member_list

    async def _get_document_snippets(self, room_id: str, query: str, limit: int = 4) -> list[dict]:
        """Retrieve document chunks for context."""
        try:
            from app.services.rag_service import RAGService
            rag_service = RAGService(self.db)
            chunks = await rag_service.semantic_search(room_id, query or "", limit=limit)
            return [
                {
                    "content": chunk.get("content", ""),
                    "page": chunk.get("page_number"),
                    "document_id": chunk.get("document_id"),
                    "similarity": chunk.get("similarity"),
                }
                for chunk in chunks
            ]
        except Exception as e:
            print(f"[AICoordinator] Failed to fetch documents: {e}")
            return []

    async def gather_room_context(self, room_id: str) -> dict:
        """Gather all relevant context for a room."""
        from app.services.goal_service import GoalService
        from app.services.kb_service import KBService
        from app.services.message_service import MessageService
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
                {'title': task.title, 'status': task.status, 'assignee': task.assignee_name}
                for task in tasks if task.status != 'done'
            ]
            
            # Get goals
            goal_service = GoalService(self.db)
            goals = await goal_service.get_room_goals(room_id)
            context['goals'] = [{'title': goal.title, 'priority': goal.priority} for goal in goals]
            
            # Get KB
            kb_service = KBService(self.db)
            kb = await kb_service.get_room_kb(room_id)
            if kb:
                context['knowledge_base'] = {
                    'summary': kb.summary,
                    'key_decisions': kb.key_decisions or [],
                }
            
            # Get room info
            room = await self.db.rooms.find_one({"id": room_id})
            if room:
                context['room_name'] = room.get('name', 'Unknown Room')
                context['custom_ai_instructions'] = room.get('custom_ai_instructions')
            
            # Get room members
            context['room_members'] = await self._get_room_members(room_id)
                
        except Exception as e:
            print(f"[AICoordinator] Error gathering context: {e}")
        
        return context

    async def handle_message(
        self,
        room_id: str,
        user_id: str,
        content: str,
        message_id: str,
        reply_to_content: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Main entry point for handling messages.
        
        Orchestrates:
        1. Gather room context
        2. Execute tools (silently)
        3. Generate text response (if needed)
        
        Args:
            room_id: Room ID
            user_id: User who sent the message
            content: Message content
            message_id: Message ID
            reply_to_content: Content of replied message (if any)
            
        Returns:
            dict with:
                - action: "send_message"
                - content: Text response (or None)
                - tools_executed: List of executed tools
                - reaction: Emoji if reacted
        """
        from app.ai.gemini_client import gemini_client
        
        if not gemini_client.is_configured():
            return None

        # 1. Gather context
        context = await self.gather_room_context(room_id)
        
        # Add document snippets for RAG
        doc_snippets = await self._get_document_snippets(room_id, content)
        context['doc_snippets'] = doc_snippets

        # 2. Execute tools (silent)
        from app.ai.tool_executor import ToolExecutor
        tool_executor = ToolExecutor(self.db)
        
        tool_result = await tool_executor.execute_tools(
            room_id=room_id,
            user_id=user_id,
            content=content,
            message_id=message_id,
            room_context=context,
        )

        executed_tools = tool_result.get("tools_executed", [])
        tool_data = tool_result.get("tool_data", {})
        reaction = tool_result.get("reaction")

        print(f"[AICoordinator] Tools executed: {[t['type'] for t in executed_tools]}")

        # 3. Determine if we need a text response
        needs_response = self._should_generate_response(content, executed_tools, tool_data)
        
        if not needs_response:
            # Only tools were needed (e.g., just a reaction)
            return {
                "action": "send_message",
                "content": None,
                "tools_executed": executed_tools,
                "reaction": reaction,
            }

        # 4. Generate text response
        from app.ai.chat_responder import chat_responder

        # Enrich context with tool data for the responder
        context['tool_data'] = tool_data
        
        response_text = await chat_responder.generate_response(
            user_message=content,
            room_context=context,
            tool_results=executed_tools,
            reply_to_content=reply_to_content,
        )

        return {
            "action": "send_message",
            "content": response_text,
            "tools_executed": executed_tools,
            "reaction": reaction,
        }

    def _should_generate_response(
        self,
        content: str,
        executed_tools: list[dict],
        tool_data: dict,
    ) -> bool:
        """
        Determine if a text response should be generated.
        
        Returns False if:
        - Only a reaction was added
        - The tools provide the full answer (e.g., translation, summary)
        
        Returns True if:
        - User asked a question
        - Tasks were created/updated (should acknowledge)
        - Web/doc search was done (should present results)
        - General conversation requiring response
        """
        # If only a reaction, no text needed
        if executed_tools and all(t.get("type") == "reaction" for t in executed_tools):
            return False

        # If tools returned data, we need to present it
        if tool_data:
            return True

        # If tasks were created/updated, acknowledge it
        if any(t.get("type") in ["task_created", "task_updated"] for t in executed_tools):
            return True

        # Check for question markers
        if '?' in content:
            return True

        # Check for common interaction triggers
        content_lower = content.lower()
        triggers = ['help', 'explain', 'what', 'how', 'why', 'when', 'where', 'can you', 'please']
        if any(trigger in content_lower for trigger in triggers):
            return True

        # Check for AI mentions
        ai_mentions = ['veya', 'ai', 'assistant', '@ai', '@veya']
        if any(mention in content_lower for mention in ai_mentions):
            return True

        # Default to generating a response
        return True


# Convenience function for backwards compatibility
async def create_coordinator(db: AsyncIOMotorDatabase) -> AICoordinator:
    """Create an AI coordinator instance."""
    return AICoordinator(db)
