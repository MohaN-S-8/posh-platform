from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Create the FastAPI app
app = FastAPI(
    title="POSH Training Platform API",
    description="API for POSH Training Platform",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI — visit this in browser to test APIs
    redoc_url="/redoc",
)

# CORS — allows the React frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint — used by Docker and CI to verify the app is running
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}


# Root endpoint
@app.get("/")
async def root():
    return {"message": "POSH Platform API is running. Visit /docs for API documentation."}
