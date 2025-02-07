from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up AIQLeads backend...")
    yield
    # Shutdown
    print("Shutting down AIQLeads backend...")

app = FastAPI(
    title="AIQLeads API",
    description="API for AI-powered lead generation and qualification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from routes import leads, auth, analytics

# Register routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(leads.router, prefix="/leads", tags=["Leads"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

@app.get("/")
async def root():
    return {
        "status": "online",
        "version": app.version,
        "documentation": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)