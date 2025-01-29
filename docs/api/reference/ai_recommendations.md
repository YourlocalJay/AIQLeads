# AI Recommendations API

This document provides detailed documentation for the AI Recommendations API endpoints.

## Get Recommendations

```http
GET /v1/recommendations
```

Get recommendations for leads based on specified criteria.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| limit | integer | Maximum number of recommendations to return. Default: 10 |
| offset | integer | Number of recommendations to skip. Default: 0 |
| score_min | float | Minimum recommendation score (0-100). Default: 0 |
| type | string | Type of recommendations: `lead`, `market`, `action` |

### Response

```json
{
  "data": [
    {
      "id": "rec_123abc",
      "type": "recommendation",
      "score": 92.5,
      "lead_id": "lead_456def",
      "created_at": "2025-01-28T12:00:00Z",
      "insights": [
        {
          "type": "market_signal",
          "description": "High engagement in similar market segments"
        }
      ],
      "actions": [
        {
          "type": "follow_up",
          "priority": "high",
          "description": "Schedule demonstration"
        }
      ]
    }
  ],
  "meta": {
    "total": 45,
    "limit": 10,
    "offset": 0
  }
}
```

## Get Recommendation by ID

```http
GET /v1/recommendations/{id}
```

Get detailed information about a specific recommendation.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | string | Unique recommendation identifier |

### Response

```json
{
  "data": {
    "id": "rec_123abc",
    "type": "recommendation",
    "score": 92.5,
    "lead_id": "lead_456def",
    "created_at": "2025-01-28T12:00:00Z",
    "insights": [
      {
        "type": "market_signal",
        "description": "High engagement in similar market segments"
      }
    ],
    "actions": [
      {
        "type": "follow_up",
        "priority": "high",
        "description": "Schedule demonstration"
      }
    ],
    "metadata": {
      "model_version": "v2.1.0",
      "confidence": 0.95,
      "features_used": [
        "engagement_score",
        "market_segment",
        "company_size"
      ]
    }
  }
}
```

## Generate Recommendations

```http
POST /v1/recommendations/generate
```

Generate new recommendations for specified leads.

### Request Body

```json
{
  "lead_ids": ["lead_456def", "lead_789ghi"],
  "options": {
    "include_insights": true,
    "min_confidence": 0.8,
    "max_recommendations": 5
  }
}
```

### Response

```json
{
  "data": {
    "job_id": "job_xyz789",
    "status": "processing",
    "estimated_completion": "2025-01-28T12:05:00Z",
    "progress": {
      "total_leads": 2,
      "processed": 0,
      "pending": 2
    }
  }
}
```

## Update Recommendation

```http
PATCH /v1/recommendations/{id}
```

Update specific fields of a recommendation.

### Request Body

```json
{
  "feedback": {
    "accuracy": 0.9,
    "usefulness": 0.85,
    "notes": "Very relevant insights"
  },
  "status": "implemented"
}
```

### Response

```json
{
  "data": {
    "id": "rec_123abc",
    "type": "recommendation",
    "score": 92.5,
    "status": "implemented",
    "feedback": {
      "accuracy": 0.9,
      "usefulness": 0.85,
      "notes": "Very relevant insights",
      "submitted_at": "2025-01-28T13:00:00Z"
    }
  }
}
```

## List Recommendation Models

```http
GET /v1/recommendations/models
```

List available recommendation models and their configurations.

### Response

```json
{
  "data": [
    {
      "id": "model_abc123",
      "version": "v2.1.0",
      "type": "lead_scoring",
      "status": "active",
      "features": [
        "engagement_score",
        "market_segment",
        "company_size"
      ],
      "performance": {
        "accuracy": 0.92,
        "precision": 0.89,
        "recall": 0.94
      },
      "last_trained": "2025-01-15T00:00:00Z"
    }
  ]
}
```

## Errors

See the [Error Handling Guide](../guides/error_handling.md) for details on error responses.