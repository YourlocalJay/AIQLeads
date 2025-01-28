from datetime import datetime, timezone
from typing import Dict, Any, List
import logging
from statistics import mean, median
from collections import Counter

from app.features.base import BaseFeatureExtractor, ValidationError
from app.core.metrics import FEATURE_EXTRACTION_TIME, FEATURE_COUNT

logger = logging.getLogger(__name__)

class LeadBehaviorExtractor(BaseFeatureExtractor):
    """
    Extracts features related to lead behavior and interaction patterns.
    
    Features extracted:
    - View counts and frequencies
    - Interaction durations
    - Time-based patterns
    - Action sequences
    - Engagement scores
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.min_interactions = config.get('min_interactions', 1)
        self.max_interaction_gap = config.get('max_interaction_gap_hours', 72)
        self.engagement_weights = config.get('engagement_weights', {
            'view': 1.0,
            'click': 2.0,
            'inquiry': 3.0,
            'message': 4.0,
            'schedule': 5.0
        })
        
    async def _compute_features(self, lead_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute behavioral features from lead interaction data.
        
        Args:
            lead_data: Dictionary containing:
                - interactions: List of interaction events
                - first_seen: Initial interaction timestamp
                - last_seen: Most recent interaction timestamp
                
        Returns:
            Dictionary of computed features
        """
        try:
            with FEATURE_EXTRACTION_TIME.labels(extractor_type='lead_behavior').time():
                # Validate required fields
                self._validate_lead_data(lead_data)
                
                # Extract interaction data
                interactions = lead_data['interactions']
                first_seen = datetime.fromisoformat(lead_data['first_seen'])
                last_seen = datetime.fromisoformat(lead_data['last_seen'])
                
                # Compute core features
                features = {
                    # Interaction counts
                    'total_interactions': len(interactions),
                    'unique_action_types': len(set(i['action'] for i in interactions)),
                    
                    # Time-based features
                    'days_since_first': (datetime.now(timezone.utc) - first_seen).days,
                    'days_since_last': (datetime.now(timezone.utc) - last_seen).days,
                    'interaction_timespan_days': (last_seen - first_seen).days,
                    
                    # Action type frequencies
                    **self._compute_action_frequencies(interactions),
                    
                    # Temporal patterns
                    **self._compute_temporal_patterns(interactions),
                    
                    # Engagement metrics
                    **self._compute_engagement_metrics(interactions),
                    
                    # Session metrics
                    **self._compute_session_metrics(interactions)
                }
                
                FEATURE_COUNT.labels(extractor_type='lead_behavior').inc(len(features))
                return features
                
        except Exception as e:
            logger.error(f"Feature extraction failed for lead behavior: {str(e)}", exc_info=True)
            raise
            
    def _validate_lead_data(self, lead_data: Dict[str, Any]) -> None:
        """Validate lead data structure"""
        required_fields = ['interactions', 'first_seen', 'last_seen']
        missing_fields = [f for f in required_fields if f not in lead_data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
            
        if not isinstance(lead_data['interactions'], list):
            raise ValidationError("Interactions must be a list")
            
        if len(lead_data['interactions']) < self.min_interactions:
            raise ValidationError(f"Must have at least {self.min_interactions} interactions")
            
    def _compute_action_frequencies(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute frequency features for different action types"""
        action_counts = Counter(i['action'] for i in interactions)
        total = len(interactions)
        
        return {
            f'{action}_frequency': count / total
            for action, count in action_counts.items()
        }
        
    def _compute_temporal_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract temporal pattern features from interactions"""
        # Convert timestamps to datetime objects
        timestamps = [
            datetime.fromisoformat(i['timestamp'])
            for i in interactions
        ]
        
        # Hour of day distribution
        hours = [t.hour for t in timestamps]
        
        # Day of week distribution (0 = Monday, 6 = Sunday)
        days = [t.weekday() for t in timestamps]
        
        return {
            'peak_hour': max(Counter(hours).items(), key=lambda x: x[1])[0],
            'peak_day': max(Counter(days).items(), key=lambda x: x[1])[0],
            'weekend_ratio': sum(1 for d in days if d >= 5) / len(days),
            'business_hours_ratio': sum(1 for h in hours if 9 <= h <= 17) / len(hours)
        }
        
    def _compute_engagement_metrics(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute engagement metrics based on interaction types and weights"""
        scores = [
            self.engagement_weights.get(i['action'], 0.0)
            for i in interactions
        ]
        
        return {
            'engagement_score_total': sum(scores),
            'engagement_score_avg': mean(scores),
            'engagement_score_median': median(scores)
        }
        
    def _compute_session_metrics(self, interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute metrics related to interaction sessions"""
        if len(interactions) < 2:
            return {
                'avg_session_length_minutes': 0.0,
                'total_sessions': 1,
                'avg_actions_per_session': len(interactions)
            }
            
        # Sort interactions by timestamp
        sorted_interactions = sorted(
            interactions,
            key=lambda x: datetime.fromisoformat(x['timestamp'])
        )
        
        # Identify sessions (gap > max_interaction_gap hours = new session)
        sessions = []
        current_session = [sorted_interactions[0]]
        
        for curr, next_int in zip(sorted_interactions, sorted_interactions[1:]):
            curr_time = datetime.fromisoformat(curr['timestamp'])
            next_time = datetime.fromisoformat(next_int['timestamp'])
            
            if (next_time - curr_time).total_seconds() / 3600 > self.max_interaction_gap:
                sessions.append(current_session)
                current_session = []
            current_session.append(next_int)
            
        if current_session:
            sessions.append(current_session)
            
        # Compute session metrics
        session_lengths = []
        for session in sessions:
            start = datetime.fromisoformat(session[0]['timestamp'])
            end = datetime.fromisoformat(session[-1]['timestamp'])
            length_minutes = (end - start).total_seconds() / 60
            session_lengths.append(length_minutes)
            
        return {
            'avg_session_length_minutes': mean(session_lengths),
            'total_sessions': len(sessions),
            'avg_actions_per_session': len(interactions) / len(sessions)
        }