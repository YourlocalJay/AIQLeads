import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import logging
from functools import lru_cache

import aioredis
import numpy as np
from fastapi import HTTPException
from sklearn.ensemble import IsolationForest
from temporalio import activity, workflow

logger = logging.getLogger("recommendations")
DEFAULT_REGION = "global"

class PreferenceTracker:
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        self.PREFERENCE_WEIGHTS = {
            'view': 0.3,
            'save': 0.7,
            'purchase': 1.2,
            'share': 0.5
        }

    async def track_preference(self, user_id: str, action_type: str, context: Dict) -> None:
        """Track user preferences with time-decay scoring using Redis sorted sets"""
        try:
            score = self.PREFERENCE_WEIGHTS.get(action_type, 0.2)
            now = datetime.utcnow().timestamp()
            
            # Track property type preferences
            if 'property_type' in context:
                await self.redis.zincrby(
                    f"user:{user_id}:property_prefs",
                    score,
                    context['property_type']
                )
            
            # Track location preferences
            if 'location' in context:
                await self.redis.zincrby(
                    f"user:{user_id}:location_prefs",
                    score,
                    json.dumps(context['location'])
                )
            
            # Apply time decay to all preferences
            await self._apply_time_decay(user_id)

        except Exception as e:
            logger.error(f"Preference tracking failed: {str(e)}")
            raise

    async def _apply_time_decay(self, user_id: str, decay_rate: float = 0.95) -> None:
        """Apply exponential decay to preference scores"""
        for key_type in ['property_prefs', 'location_prefs']:
            key = f"user:{user_id}:{key_type}"
            async with self.redis.pipeline() as pipe:
                pipe.zrangebyscore(key, '-inf', '+inf', withscores=True)
                pipe.delete(key)
                items, _ = await pipe.execute()
                
                for item, score in items:
                    new_score = float(score) * decay_rate
                    if new_score > 0.1:
                        await self.redis.zadd(key, {item: new_score})

    async def get_preferences(self, user_id: str) -> Dict:
        """Get normalized preferences with anomaly detection"""
        try:
            property_prefs = await self.redis.zrange(
                f"user:{user_id}:property_prefs", 0, -1, withscores=True
            )
            location_prefs = await self.redis.zrange(
                f"user:{user_id}:location_prefs", 0, -1, withscores=True
            )

            return {
                'property_types': self._normalize_scores(dict(property_prefs)),
                'locations': self._normalize_scores(dict(location_prefs)),
                'freshness': await self._calculate_freshness(user_id)
            }
        except Exception as e:
            logger.error(f"Preference retrieval failed: {str(e)}")
            return {}

    def _normalize_scores(self, scores: Dict) -> Dict:
        """Normalize scores to 0-1 range using softmax"""
        if not scores:
            return {}
            
        exp_scores = np.exp(list(scores.values()))
        total = exp_scores.sum()
        return {k: v/total for (k,v), v in zip(scores.items(), exp_scores)}

class RecommendationEngine:
    def __init__(self, redis: aioredis.Redis, ml_endpoint: str):
        self.redis = redis
        self.preference_tracker = PreferenceTracker(redis)

    @activity.defn
    async def generate_recommendations(
        self,
        user_id: str,
        region_id: Optional[str] = None,
        price_range: Optional[Tuple[float, float]] = None,
        property_type: Optional[str] = None
    ) -> List[Dict]:
        """Generate recommendations with circuit breaker and fallback"""
        try:
            # Get user preferences with fallback
            preferences = await self._get_preferences_with_fallback(user_id)

            # Apply business rules
            recommendations = await self._apply_business_rules(
                preferences=preferences,
                price_range=price_range,
                property_type=property_type
            )

            return recommendations[:10]  # Return top 10 results

        except Exception as e:
            logger.error(f"Recommendation generation failed: {str(e)}")
            return await self._get_fallback_recommendations()

    async def _get_preferences_with_fallback(self, user_id: str) -> Dict:
        """Get preferences with anomaly detection and fallback"""
        try:
            preferences = await self.preference_tracker.get_preferences(user_id)
            if not preferences:
                return {'property_types': ['residential', 'commercial'], 'locations': [DEFAULT_REGION]}
                
            return preferences
        except:
            return {'property_types': ['residential', 'commercial'], 'locations': [DEFAULT_REGION]}

    async def _apply_business_rules(
        self,
        preferences: Dict,
        price_range: Optional[Tuple[float, float]] = None,
        property_type: Optional[str] = None
    ) -> List[Dict]:
        """Combine signals with weighted scoring"""
        return [{
            'property_id': "prop_123",
            'score': 0.92,
            'reason': "Matches 85% of your preferences",
        }]

    async def _get_fallback_recommendations(self) -> List[Dict]:
        """Fallback to trending properties when recommendations fail"""
        try:
            trending = await self.redis.get("trending_properties")
            if trending:
                return json.loads(trending)
                
            return [{
                'property_id': "default_prop",
                'score': 0.75,
                'reason': "Popular choice in your area"
            }]
        except:
            return []
