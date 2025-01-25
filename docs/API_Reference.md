# AIQLeads API Reference

## Core Features

### Authentication and Authorization
[Previous authentication content...]

## Dynamic Pricing Endpoints

### Get Lead Price
**GET /api/v1/pricing/lead/{lead_id}**

Returns dynamically calculated price for a specific lead based on market demand and user tier.

#### Request Parameters
```json
{
  "lead_id": "uuid-v4",
  "user_tier": "standard|pro|enterprise",
  "location": "string",
  "property_type": "string"
}
```

#### Response
```json
{
  "base_price": 125.00,
  "tier_discount": 15.00,
  "final_price": 110.00,
  "demand_multiplier": 1.2,
  "valid_until": "2025-01-25T14:00:00Z"
}
```

## Recommendation Engine

### Get Personalized Recommendations
**GET /api/v1/recommendations**

Returns personalized lead recommendations based on user history and preferences.

#### Request Parameters
```json
{
  "user_id": "uuid-v4",
  "location": "string",
  "price_range": {
    "min": 0,
    "max": 1000000
  },
  "property_types": ["single_family", "multi_family", "commercial"],
  "limit": 20
}
```

#### Response
```json
{
  "recommendations": [{
    "lead_id": "uuid-v4",
    "score": 0.95,
    "match_factors": ["location", "price_range", "property_type"],
    "price": 125.00,
    "expiration": "2025-01-25T14:00:00Z"
  }],
  "metadata": {
    "total_matches": 45,
    "page_size": 20,
    "next_page_token": "string"
  }
}
```

## Fraud Detection

### Validate Lead
**POST /api/v1/leads/validate**

Performs comprehensive lead validation including fraud detection.

#### Request Body
```json
{
  "lead_data": {
    "contact_info": {
      "email": "string",
      "phone": "string"
    },
    "property_details": {
      "address": "string",
      "price": 500000,
      "listing_type": "string"
    },
    "metadata": {
      "source": "string",
      "capture_timestamp": "2025-01-25T12:00:00Z"
    }
  }
}
```

#### Response
```json
{
  "validation_result": {
    "is_valid": true,
    "fraud_score": 0.05,
    "confidence": 0.95,
    "checks_passed": [
      "contact_validation",
      "property_verification",
      "duplicate_detection"
    ],
    "warnings": []
  },
  "metadata": {
    "processing_time": "150ms",
    "validation_timestamp": "2025-01-25T12:00:01Z"
  }
}
```

## Performance Considerations

### Rate Limits
- Standard Tier: 100 requests/minute
- Pro Tier: 500 requests/minute
- Enterprise Tier: 2000 requests/minute

### Caching
- Price calculations: 5-minute cache
- Recommendations: 15-minute cache
- Validation results: 24-hour cache

### Monitoring
- Response time threshold: 200ms
- Error rate threshold: 1%
- Cache hit rate target: 85%
