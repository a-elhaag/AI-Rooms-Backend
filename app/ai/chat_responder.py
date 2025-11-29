"""
Chat Responder LLM - Generates user-facing text responses only.

This LLM is ONLY responsible for generating natural language responses to users.
It has NO access to tools. Tool execution is handled separately by the ToolExecutor.
"""

from typing import Optional

from app.ai.gemini_client import gemini_client


class ChatResponder:
    """
    LLM dedicated to generating user-facing chat responses.
    
    This is separate from the ToolExecutor to ensure clean separation of concerns:
    - ChatResponder: Generates natural, conversational text responses
    - ToolExecutor: Silently triggers tools (tasks, reactions, searches)
    """

    def __init__(self):
        pass

    async def generate_response(
        self,
        user_message: str,
        room_context: dict,
        tool_results: Optional[list[dict]] = None,
        reply_to_content: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate a natural language response to the user.

        Args:
            user_message: The user's message
            room_context: Context about the room (members, goals, tasks, KB)
            tool_results: Results from tools that were executed (for reference)
            reply_to_content: Content of message being replied to (if any)

        Returns:
            str: The AI's text response, or None if no response needed
        """
        if not gemini_client.is_configured():
            return None

        # Build the system instruction
        system_instruction = self._build_system_instruction(room_context, tool_results)

        # Build the user prompt
        user_prompt = user_message
        if reply_to_content:
            user_prompt = f'[Replying to: "{reply_to_content}"]\n\n{user_message}'

        # Build conversation history
        history = self._build_history(room_context)

        try:
            chat = await gemini_client.create_chat(
                history=history,
                system_instruction=system_instruction,
                tools=None,  # NO TOOLS - this is key!
            )

            if not chat:
                return None

            response = chat.send_message(user_prompt)
            return response.text if hasattr(response, 'text') else None

        except Exception as e:
            print(f"[ChatResponder] Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return "I had trouble thinking of a response. Could you try again?"

    def _build_system_instruction(
        self,
        room_context: dict,
        tool_results: Optional[list[dict]] = None,
    ) -> str:
        """Build the system instruction for the chat responder."""
        
        member_names = [m['username'] for m in room_context.get('room_members', [])]
        
        parts = [
            "# IDENTITY",
            "You are Veya, a friendly AI teammate in a collaborative workspace.",
            "You were created for AI-Rooms by Anas, Sohaila, Youstina, and Ruba.",
            "",
            "# YOUR ROLE",
            "Your ONLY job is to respond conversationally to users.",
            "You DO NOT have access to any tools - another system handles tool execution.",
            "Focus purely on being helpful, friendly, and informative in your responses.",
            "",
            "# PERSONALITY",
            "- Warm, helpful, and genuinely interested in the team's success",
            "- Speak naturally like a real teammate, not robotic or overly formal",
            "- Use casual language and contractions (I'm, you're, let's)",
            "- Be concise - match the energy and length of messages you receive",
            "- Add light humor only when the mood is casual, skip it if things seem urgent",
            "- Show enthusiasm with emojis when celebrating wins 🎉",
            "",
            "# CONTEXT",
            f"Room: {room_context.get('room_name', 'AI Room')}",
            f"Team members: {', '.join(member_names)}" if member_names else "",
        ]

        # Add goal context
        if room_context.get('goals'):
            goals_text = ", ".join([g['title'] for g in room_context['goals'][:3]])
            parts.append(f"Room goals: {goals_text}")

        # Add custom instructions if present
        if room_context.get('custom_ai_instructions'):
            parts.append(f"\n⚡ PRIORITY INSTRUCTIONS:\n{room_context['custom_ai_instructions']}")

        # Add active tasks info
        if room_context.get('active_tasks'):
            task_lines = []
            for t in room_context['active_tasks'][:5]:
                assignee = f" ({t['assignee']})" if t.get('assignee') else ""
                task_lines.append(f"  - {t['title']}{assignee} [{t['status']}]")
            parts.append("\nActive tasks:\n" + "\n".join(task_lines))

        # Add Knowledge Base context
        kb = room_context.get('knowledge_base')
        if kb:
            if kb.get('summary'):
                parts.append(f"\n📚 Knowledge Base: {kb['summary']}")

        # Add document snippets if available
        if room_context.get('doc_snippets'):
            snippet_lines = []
            for idx, snip in enumerate(room_context['doc_snippets']):
                page_info = f" (page {snip['page']})" if snip.get('page') else ""
                snippet = snip.get('content', '')[:400]
                snippet_lines.append(f"[Doc {idx+1}{page_info}] {snippet}")
            parts.append("\n📄 Relevant document excerpts:\n" + "\n".join(snippet_lines))

        # Add tool results context if tools were executed
        if tool_results:
            parts.append("\n# ACTIONS TAKEN BY SYSTEM")
            parts.append("The following actions were automatically executed:")
            for result in tool_results:
                if result.get("type") == "task_created":
                    task = result.get("data", {})
                    parts.append(f"- ✅ Created task: '{task.get('title', 'Unknown')}'")
                elif result.get("type") == "task_updated":
                    task = result.get("data", {})
                    parts.append(f"- ✅ Updated task: '{task.get('title', 'Unknown')}'")
                elif result.get("type") == "reaction":
                    parts.append(f"- Reacted with {result.get('emoji', '👍')}")
                elif result.get("type") == "web_search":
                    parts.append(f"- 🔍 Searched the web")
                elif result.get("type") == "document_search":
                    parts.append(f"- 📄 Searched documents")
            parts.append("\nMention these actions naturally in your response if relevant.")

        parts.extend([
            "",
            "# RESPONSE STYLE",
            "- Keep responses SHORT unless detail is needed",
            "- Start directly, no 'Veya:' prefix",
            "- Skip meta-acknowledgments like 'I saw your message'",
            "- Use **bold** for emphasis and `code` when relevant",
            "- Be helpful and answer questions to the best of your knowledge",
            "- If you created/updated tasks, mention it naturally: 'Added that to our board!'",
            "",
            "# EXAMPLES",
            "User: 'What's the capital of France?'",
            "→ 'Paris! 🇫🇷 Need anything else?'",
            "",
            "User: 'I'll finish the login page by Friday' (task was created)",
            "→ 'Got it! Added to the board. Let me know if you need help!'",
            "",
            "User: 'Just deployed the new feature!'",
            "→ 'Amazing work! 🚀'",
        ])

        return "\n".join(parts)

    def _build_history(self, room_context: dict) -> list[dict]:
        """Build conversation history from room context."""
        history = []
        recent_messages = room_context.get('recent_messages', [])
        
        for msg in recent_messages[-8:]:  # Last 8 messages
            if ': ' in msg:
                name, text = msg.split(': ', 1)
                role = 'model' if name.lower() in ['ai', 'assistant', 'bot', 'ai assistant', 'veya'] else 'user'
                history.append({
                    'role': role,
                    'parts': [text]
                })
        
        return history


# Global instance
chat_responder = ChatResponder()
