"""
Utility evaluator for choosing best action from candidates.
"""
from typing import Any


class UtilityEvaluator:
    """
    Evaluates candidate actions and chooses the best one based on utility.
    
    Uses a combination of heuristics and LLM reasoning to score
    different possible actions and choose the most useful one.
    """
    
    def __init__(self):
      """
    Initialize utility evaluator.

      """
    self.llm = None
    self.scoring_prompt = None
    self.criteria = {}

   
def choose_action(self, candidates: list[dict], context: dict) -> dict:
    """
    Randomly pick an action (testing only).
    """
    if not candidates:
        return {}

    return random.choice(candidates)

    
    def _score_candidate(
        self,
        candidate: dict,
        context: dict
    ) -> float:
        """
        Score a single candidate action.
        
        Args:
            candidate: Candidate action
            context: Room context
            
        Returns:
            float: Utility score (0-1)
            
        TODO:
            - Calculate heuristic score
            - Optionally use LLM for complex evaluation
            - Return score
        """
        pass
    
    async def _llm_evaluate(self, candidates, context):
     if not candidates:
        return {}

    # simple heuristic: pick candidate with longest reasoning
    return max(candidates, key=lambda c: len(c.get("reasoning", "")))

