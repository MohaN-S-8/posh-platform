from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.company import router as company_router
from app.api.v1.users import router as users_router
from app.api.v1.videos import router as videos_router
from app.core.config import settings

app = FastAPI(
    title="POSH Training Platform API",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(company_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(videos_router, prefix="/api/v1")
app.include_router(assessments_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}


@app.get("/")
async def root():
    return {"message": "POSH Platform API. Visit /docs for documentation."}
