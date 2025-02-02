"""
Core AI Processor using Fireworks AI
"""
import httpx
from typing import Dict, Any, List
import json
from ..core.config import (
    FIREWORKS_API_KEY,
    FIREWORKS_MODEL,
    FIREWORKS_MAX_TOKENS,
    SCORING_WEIGHTS
)

class LeadProcessor:
    def __init__(self):
        self.api_key = FIREWORKS_API_KEY
        self.model = FIREWORKS_MODEL
        self.client = httpx.AsyncClient()
        self.weights = SCORING_WEIGHTS

    async def score_lead(self, lead_data: Dict[str, Any]) -> float:
        """Basic lead scoring using weighted factors"""
        score = 0.0
        for factor, weight in self.weights.items():
            if factor in lead_data:
                score += lead_data[factor] * weight
        return min(max(score, 0), 100)  # Normalize to 0-100

    async def analyze_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Basic property analysis"""
        prompt = self._build_property_prompt(property_data)
        
        response = await self.client.post(
            "https://api.fireworks.ai/inference/v1/complete",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "prompt": prompt,
                "max_tokens": FIREWORKS_MAX_TOKENS,
                "temperature": 0.7
            }
        )
        
        if response.status_code != 200:
            return {"error": "Analysis failed", "details": response.text}
            
        analysis = response.json()
        return self._parse_analysis(analysis)

    async def get_market_trends(self, location: str) -> Dict[str, Any]:
        """Basic market trend analysis"""
        return {
            "trend": "stable",
            "confidence": 0.8,
            "factors": ["price", "inventory"]
        }

    def _build_property_prompt(self, property_data: Dict[str, Any]) -> str:
        """Builds AI prompt for property analysis"""
        return f"""
        Analyze this property:
        Location: {property_data.get('location', 'Unknown')}
        Price: ${property_data.get('price', 0):,}
        Type: {property_data.get('type', 'Unknown')}
        Features: {', '.join(property_data.get('features', []))}
        
        Provide a brief analysis including:
        1. Market position
        2. Key selling points
        3. Potential concerns
        """

    def _parse_analysis(self, raw_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Parses AI response into structured data"""
        try:
            text = raw_analysis.get("choices", [{}])[0].get("text", "")
            # Basic parsing for MVP
            return {
                "summary": text,
                "score": self._extract_score(text)
            }
        except Exception as e:
            return {"error": str(e)}

    def _extract_score(self, text: str) -> float:
        """Extracts numerical score from analysis text"""
        # Simple scoring for MVP
        positive_indicators = ["excellent", "good", "great"]
        negative_indicators = ["poor", "bad", "concerns"]
        
        score = 70.0  # Base score
        for word in positive_indicators:
            if word in text.lower():
                score += 5
        for word in negative_indicators:
            if word in text.lower():
                score -= 5
                
        return min(max(score, 0), 100)  # Normalize to 0-100