# AIQLeads API Documentation

## Authentication
All endpoints require JWT authentication.

## Rate Limiting
- Default: 1000 requests/hour
- Enterprise: 5000 requests/hour

## Endpoints
### /api/v1/leads
- GET: List leads
- POST: Create lead
- PUT: Update lead
- DELETE: Remove lead

### Error Handling
- 400: Bad Request
- 401: Unauthorized
- 429: Rate Limited
- 500: Server Error

## Validation
All requests validate against JSON schemas in /schemas