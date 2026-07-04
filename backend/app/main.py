from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.analytics import router as analytics_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.certificates import router as certificates_router
from app.api.v1.company import router as company_router
from app.api.v1.hr import router as hr_router
from app.api.v1.users import router as users_router
from app.api.v1.videos import router as videos_router
from app.core.config import settings

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="POSH Training Platform API", version="1.0.0", docs_url="/docs")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
app.include_router(hr_router, prefix="/api/v1")
app.include_router(certificates_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")

# Add this function + event to main.py


@app.on_event("startup")
async def run_seed_on_startup():
    """
    Runs seed only if tables are empty.
    Idempotent — safe to run every time Docker starts.
    """
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(text("SELECT COUNT(*) FROM role_master"))
        count = result.scalar()
        if count > 0:
            return  # already seeded, skip

        # Roles
        await db.execute(
            text(
                """
            INSERT IGNORE INTO role_master (role_id, role_name)
            VALUES (1,'Super Admin'),(2,'Company Admin'),(3,'HR'),(4,'Employee')
        """
            )
        )

        # Default company
        await db.execute(
            text(
                """
            INSERT IGNORE INTO company_master
                (company_id, company_code, company_name, status)
            VALUES (1, 'DEFAULT', 'POSH Platform', 'Active')
        """
            )
        )

        # Languages
        await db.execute(
            text(
                """
            INSERT IGNORE INTO language_master (language_id, language_name)
            VALUES (1,'English'),(2,'Hindi'),(3,'Tamil'),
                   (4,'Telugu'),(5,'Malayalam'),(6,'Kannada')
        """
            )
        )

        # Video categories
        await db.execute(
            text(
                """
            INSERT IGNORE INTO video_category (category_id, category_name)
            VALUES (1,'POSH Awareness'),(2,'Workplace Conduct'),
                   (3,'Case Studies'),(4,'Reporting Procedures'),(5,'Annual Refresher')
        """
            )
        )

        # Default Super Admin user (change email/password after first login)
        from app.core.security import hash_password

        await db.execute(
            text(
                """
            INSERT IGNORE INTO user_master
                (user_id, company_id, employee_id, first_name, last_name,
                 email, mobile, role_id, username, password_hash, status, is_deleted)
            VALUES
                (1, 1, 'ADMIN001', 'Super', 'Admin',
                 'admin@posh.com', '9000000001', 1,
                 'admin@posh.com', :pwd, 'Active', 'N'),
                (2, 1, 'HR001', 'HR', 'Manager',
                 'hr@posh.com', '9000000002', 3,
                 'hr@posh.com', :pwd, 'Active', 'N')
        """
            ),
            {"pwd": hash_password("Admin@1234")},
        )

        await db.commit()
        print("✅ Auto-seed complete")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}


@app.get("/")
async def root():
    return {"message": "POSH Platform API. Visit /docs for documentation."}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


app.add_middleware(SecurityHeadersMiddleware)
