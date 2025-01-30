# AIQLeads API Documentation

## Lead Management API

### Lead Creation
`POST /api/v1/leads`
- Creates new leads with AI-powered scoring
- Supports batch processing
- Includes fraud detection

### Lead Updates
`PUT /api/v1/leads/{id}`
- Updates lead information
- Triggers real-time notifications
- Updates AI scoring

## Market Insight API

### Market Analysis
`GET /api/v1/market/analysis`
- Provides AI-driven market forecasts
- Includes regional comparisons
- Returns trend analysis

### Geospatial Data
`GET /api/v1/geo/clusters`
- Returns cluster visualizations
- Includes density heatmaps
- Provides competitor analysis

## AI Recommendations API

### User Preferences
`GET /api/v1/preferences`
- Returns personalized recommendations
- Includes behavioral analysis
- Provides market predictions

## WebSocket API

### Real-time Updates
`ws://api/v1/updates`
- Provides real-time lead updates
- Sends market changes
- Delivers system alerts
