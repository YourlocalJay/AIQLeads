# Lead Behavior Feature Extractor

The Lead Behavior Feature Extractor analyzes lead interaction patterns to generate behavioral features for the AI recommendation system.

## Features Generated

### Core Metrics
- `total_interactions`: Total number of recorded interactions
- `unique_action_types`: Number of different action types performed
- `days_since_first`: Days since first interaction
- `days_since_last`: Days since last interaction
- `interaction_timespan_days`: Total timespan of interactions

### Action Frequencies
For each action type (view, click, inquiry, message, schedule):
- `{action}_frequency`: Proportion of interactions of this type

### Temporal Patterns
- `peak_hour`: Hour of day with most activity (0-23)
- `peak_day`: Day of week with most activity (0=Monday, 6=Sunday)
- `weekend_ratio`: Proportion of activity on weekends
- `business_hours_ratio`: Proportion of activity during business hours

### Engagement Metrics
- `engagement_score_total`: Weighted sum of all interactions
- `engagement_score_avg`: Average engagement score per interaction
- `engagement_score_median`: Median engagement score

### Session Metrics
- `avg_session_length_minutes`: Average length of interaction sessions
- `total_sessions`: Number of distinct interaction sessions
- `avg_actions_per_session`: Average actions per session

## Usage Example

```python
from app.features.lead_behavior import LeadBehaviorExtractor
from app.core.config import settings

async def analyze_lead_behavior(lead_id: str):
    # Initialize extractor with default config
    extractor = LeadBehaviorExtractor(settings.LEAD_BEHAVIOR_CONFIG)
    
    # Example lead data
    lead_data = {
        'interactions': [
            {
                'action': 'view',
                'timestamp': '2025-01-27T10:30:00Z'
            },
            {
                'action': 'click',
                'timestamp': '2025-01-27T10:35:00Z'
            },
            {
                'action': 'inquiry',
                'timestamp': '2025-01-27T14:20:00Z'
            }
        ],
        'first_seen': '2025-01-27T10:30:00Z',
        'last_seen': '2025-01-27T14:20:00Z'
    }
    
    # Extract features
    features = await extractor.extract(lead_data)
    return features
```

## Configuration

The extractor can be configured through `settings.LEAD_BEHAVIOR_CONFIG`:

```python
LEAD_BEHAVIOR_CONFIG = {
    'min_interactions': 1,          # Minimum interactions required
    'max_interaction_gap_hours': 72,  # Maximum gap between session interactions
    'engagement_weights': {         # Weights for different actions
        'view': 1.0,
        'click': 2.0,
        'inquiry': 3.0,
        'message': 4.0,
        'schedule': 5.0
    },
    'business_hours': {
        'start': 9,  # 9 AM
        'end': 17,   # 5 PM
    },
    'cache_ttl': 3600  # Cache timeout in seconds
}
```

## Performance Considerations

1. Caching
   - Features are cached by default for 1 hour
   - Cache key includes the full lead data hash
   - Redis is used as the cache backend

2. Batch Processing
   - Use `extract_batch()` for multiple leads
   - Default batch size is 100
   - Concurrent processing with asyncio

3. Monitoring
   - Prometheus metrics for extraction time
   - Cache hit/miss rates tracked
   - Error rates monitored

## Error Handling

The extractor implements comprehensive validation:

1. Required Fields
   - interactions list
   - first_seen timestamp
   - last_seen timestamp

2. Data Validation
   - Minimum number of interactions
   - Valid timestamp formats
   - Known action types

3. Error Types
   - `ValidationError`: Invalid input data
   - `FeatureExtractionError`: Computation failures

## Testing

Run the test suite:

```bash
pytest tests/features/test_lead_behavior.py -v
```

Test coverage includes:
- Basic feature extraction
- Action frequency calculations
- Temporal pattern detection
- Session identification
- Cache functionality
- Error cases