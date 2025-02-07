# AIQLeads

AI-powered lead generation and qualification platform.

## Project Structure

```
AIQLeads/
├── README.md                 # Project overview
├── .env.example             # Environment configuration
├── backend/                 # FastAPI backend
├── ai_models/              # AI and ML components
├── scraping/               # Web scraping infrastructure
├── services/               # Third-party integrations
├── deployment/             # Deployment configurations
└── tests/                  # Testing suite
```

## Development

### Setup

1. Clone the repository
2. Copy `.env.example` to `.env` and configure environment variables
3. Install dependencies
4. Run the development server

### Running the Application

```bash
cd backend
uvicorn main:app --reload
```

API documentation will be available at `/docs`

## Testing

```bash
python -m pytest
```

## License

MIT