import re
from typing import Optional

from app.ai.gemini_client import gemini_client


class ShouldRespondClassifier:

    def __init__(self):
        """Initialize classifier with rule patterns."""
        self.ai_triggers = [
            r"\b(hey\s+)?ai\b",
            r"\b(hey\s+)?assistant\b",
            r"\b(hey\s+)?bot\b",
            r"@ai",
            r"@assistant",
        ]

        self.question_patterns = [
            r"\bcan\s+you\b",
            r"\bcould\s+you\b",
            r"\bwill\s+you\b",
            r"\bwould\s+you\b",
            r"\bplease\b.*\?",
            r"\bhelp\s+(me|us)\b",
            r"\bwhat\s+(is|are|was|were)",
            r"\bhow\s+(do|does|can|to)",
            r"\bwhy\s+(is|are|do|does)",
            r"\bwhen\s+(is|are|do|does|should)",
            r"\bwhere\s+(is|are|do|does)",
        ]

        self.task_keywords = [
            r"\bcreate\s+a?\s+task\b",
            r"\badd\s+a?\s+task\b",
            r"\btodo\b",
            r"\bneed\s+to\s+do\b",
            r"\bremind\s+me\b",
            r"\bschedule\b",
            r"\bassign\b",
        ]

    async def should_respond(
        self, room_id: str, user_id: str, content: str, context: dict
    ) -> bool:
        # Check rule-based triggers first
        rule_result = self._check_rules(content)
        if rule_result is not None:
            return rule_result

        # If unclear, use LLM for classification
        return await self._llm_classify(content, context)

    def _check_rules(self, content: str) -> Optional[bool]:
        """
        Check rule-based triggers.

        Args:
            content: Message content

        Returns:
            Optional[bool]: True/False if rule matches, None if unclear
        """
        content_lower = content.lower()

        # Strong positive signals
        for pattern in self.ai_triggers:
            if re.search(pattern, content_lower):
                return True

        # Task-related keywords
        for pattern in self.task_keywords:
            if re.search(pattern, content_lower):
                return True

        # Questions that likely need AI
        for pattern in self.question_patterns:
            if re.search(pattern, content_lower):
                # Check if it's a question (ends with ?)
                if "?" in content:
                    return True

        # Greetings directed at AI
        if re.match(r"^(hi|hello|hey)\s+(ai|assistant|bot)", content_lower):
            return True

        # Commands
        if content_lower.startswith(("/ai", "/help", "/summarize", "/translate")):
            return True

        # If very short message (< 3 words) and no clear trigger, don't respond
        if len(content.split()) < 3:
            return False

        # Unclear - let LLM decide
        return None

    async def _llm_classify(self, content: str, context: dict) -> bool:
        """
        Use LLM to classify if AI should respond.

        Args:
            content: Message content
            context: Room context

        Returns:
            bool: True if AI should respond
        """
        if not gemini_client.is_configured():
            # Default to responding if no API key
            return True

        prompt = f"""You are analyzing a message in a group chat to decide if the AI assistant should respond.

Message: "{content}"

Recent context: {context.get('recent_messages', 'No recent messages')}

Should the AI respond to this message? Consider:
- Is it directed at the AI?
- Does it ask a question that needs assistance?
- Does it request an action (create task, search, translate, etc.)?
- Is it general conversation between humans where AI shouldn't interrupt?

Respond with ONLY 'YES' or 'NO'."""

        try:
            response = await gemini_client.generate_response(
                prompt=prompt, model="gemini-2.5-flash-lite"
            )
            return "yes" in response.lower().strip()
        except Exception as e:
            print(f"Classifier LLM error: {e}")
            # Default to not responding if error
            return False
