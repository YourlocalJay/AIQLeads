# API Reference

This section provides detailed API endpoints reference documentation for the AIQLeads platform.

## Overview

The AIQLeads API is organized around REST. Our API accepts JSON-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs.

## Base URLs

- Production: `https://api.aiqleads.com/v1`
- Staging: `https://api.staging.aiqleads.com/v1`
- Development: `https://api.dev.aiqleads.com/v1`

## Authentication

All API endpoints require authentication. AIQLeads uses API keys for authentication. Include your API key in the Authorization header:

```http
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### AI Recommendations

See [AI Recommendations API](./ai_recommendations.md) for detailed endpoint documentation.

## Error Handling

See [Error Handling Guide](../guides/error_handling.md) for detailed information about error responses and handling.

## Rate Limiting

The API implements rate limiting based on these factors:
- Basic tier: 60 requests per minute
- Professional tier: 300 requests per minute
- Enterprise tier: Custom limits

Rate limit headers are included in all API responses:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 56
X-RateLimit-Reset: 1612345678
```