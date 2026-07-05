from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.certificates import router as certificates_router
from app.api.v1.company import router as company_router
from app.api.v1.employee import router as employee_router
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
app.include_router(admin_router, prefix="/api/v1")
app.include_router(employee_router, prefix="/api/v1")


@app.on_event("startup")
async def run_seed_on_startup():
    """
    Ensure required reference data and default login users exist.
    This is intentionally idempotent so Docker restarts can repair missing seed rows.
    """
    from sqlalchemy import text

    from app.core.security import hash_password
    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await db.execute(
            text(
                """
                INSERT INTO role_master (role_id, role_name)
                VALUES
                    (1, 'Super Admin'),
                    (2, 'Company Admin'),
                    (3, 'HR'),
                    (4, 'Employee')
                ON DUPLICATE KEY UPDATE role_name = VALUES(role_name)
                """
            )
        )

        await db.execute(
            text(
                """
                INSERT INTO company_master
                    (company_id, company_code, company_name, status, is_deleted)
                VALUES
                    (1, 'DEFAULT', 'POSH Platform', 'Active', 'N')
                ON DUPLICATE KEY UPDATE
                    company_code = VALUES(company_code),
                    company_name = VALUES(company_name),
                    status = 'Active',
                    is_deleted = 'N'
                """
            )
        )

        await db.execute(
            text(
                """
                INSERT INTO language_master (language_id, language_name)
                VALUES
                    (1, 'English'),
                    (2, 'Hindi'),
                    (3, 'Tamil'),
                    (4, 'Telugu'),
                    (5, 'Malayalam'),
                    (6, 'Kannada')
                ON DUPLICATE KEY UPDATE language_name = VALUES(language_name)
                """
            )
        )

        await db.execute(
            text(
                """
                INSERT INTO video_category (category_id, category_name)
                VALUES
                    (1, 'POSH Awareness'),
                    (2, 'Workplace Conduct'),
                    (3, 'Case Studies'),
                    (4, 'Reporting Procedures'),
                    (5, 'Annual Refresher')
                ON DUPLICATE KEY UPDATE category_name = VALUES(category_name)
                """
            )
        )

        default_password_hash = hash_password("Admin@1234")
        default_users = [
            {
                "employee_id": "ADMIN001",
                "first_name": "Super",
                "last_name": "Admin",
                "email": "admin@posh.com",
                "mobile": "9000000001",
                "role_id": 1,
            },
            {
                "employee_id": "HR001",
                "first_name": "HR",
                "last_name": "Manager",
                "email": "hr@posh.com",
                "mobile": "9000000002",
                "role_id": 3,
            },
        ]

        for user in default_users:
            params = {**user, "pwd": default_password_hash}
            await db.execute(
                text(
                    """
                    UPDATE user_master
                    SET
                        company_id = 1,
                        employee_id = :employee_id,
                        first_name = :first_name,
                        last_name = :last_name,
                        email = :email,
                        mobile = :mobile,
                        role_id = :role_id,
                        username = :email,
                        password_hash = :pwd,
                        status = 'Active',
                        is_deleted = 'N'
                    WHERE
                        email = :email
                        OR username = :email
                        OR employee_id = :employee_id
                    """
                ),
                params,
            )
            await db.execute(
                text(
                    """
                    INSERT INTO user_master
                        (company_id, employee_id, first_name, last_name,
                         email, mobile, role_id, username, password_hash, status, is_deleted)
                    SELECT
                        1, :employee_id, :first_name, :last_name,
                        :email, :mobile, :role_id, :email, :pwd, 'Active', 'N'
                    WHERE NOT EXISTS (
                        SELECT 1 FROM user_master WHERE email = :email
                    )
                    """
                ),
                params,
            )

        await db.execute(
            text(
                """
                UPDATE account_lockout
                SET failed_attempts = 0, locked_until = NULL
                WHERE user_id IN (
                    SELECT user_id
                    FROM user_master
                    WHERE email IN ('admin@posh.com', 'hr@posh.com')
                )
                """
            )
        )

        await db.commit()
        print("Auto-seed complete: roles, default company, admin, and HR users are ready.")


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
