"""
Intent Fallback Handler for FRIDAY
Gracefully resolves ambiguity when user speech matches no direct automation intent.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IntentFallbackHandler:
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold

    def resolve_fallback(self, query: str, candidate_scores: Dict[str, float]) -> Optional[Dict[str, Any]]:
        if not candidate_scores:
            logger.info("No candidates provided for fallback resolution")
            return {
                "action": "clarify_intent",
                "message": f"I couldn't quite understand '{query}'. Could you repeat with more detail?",
                "query": query
            }

        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        best_intent, top_score = sorted_candidates[0]

        if top_score >= self.confidence_threshold:
            return {
                "action": best_intent,
                "confidence": top_score,
                "resolved": True
            }

        return {
            "action": "prompt_user",
            "suggested_intent": best_intent,
            "confidence": top_score,
            "message": f"Did you mean to {best_intent.replace('_', ' ')}?"
        }
