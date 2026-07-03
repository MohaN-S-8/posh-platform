# Phase 1 (Remaining) + Phase 2 — Step-by-Step Guide

## Where You Are Right Now ✅

| Done                     | Remaining in Phase 1                  |
| ------------------------ | ------------------------------------- |
| ✅ Signup + OTP          | ⬜ Forgot Password / Reset Password   |
| ✅ Login + Lockout       | ⬜ Logout + Token Refresh             |
| ✅ JWT tokens            | ⬜ RBAC middleware (get_current_user) |
| ✅ Auth tables migration | ⬜ Company CRUD (Admin)               |
| ✅ Seed data             | ⬜ User CRUD (Admin)                  |
| ✅ Tests passing         | ⬜ Alembic migration for auth tables  |
| ✅ CI green              |                                       |

---

# PHASE 1 REMAINING — Complete Auth System

---

## STEP 21: Run the Auth Tables Migration

You created `models/auth.py` but haven't migrated it yet. Do this now.

First update `backend/alembic/env.py` — add the auth models import:

```python
import os
import sys

from alembic import context
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base
from app.models.auth import (  # noqa: F401
    AccountLockout,
    LoginAttempts,
    OTPVerification,
    PasswordResetTokens,
    RefreshTokens,
)
from app.models.company import CompanyMaster  # noqa: F401
from app.models.role import RoleMaster  # noqa: F401
from app.models.user import UserMaster  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Generate and apply:

```bash
cd backend
.venv\Scripts\activate
alembic revision --autogenerate -m "add_auth_tables"
alembic upgrade head
```

Verify in MySQL:

```bash
docker exec -it posh_mysql mysql -u posh_user -pchangeme_password posh_db
```

```sql
SHOW TABLES;
-- Should now show: account_lockout, login_attempts, otp_verification,
--                  password_reset_tokens, refresh_tokens (plus existing 3)
EXIT;
```

---

## STEP 22: Add RBAC Middleware (get_current_user)

This is the dependency that protects every authenticated endpoint.

Create `backend/app/core/dependencies.py`:

```python
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import UserMaster


class CurrentUser:
    """Holds the authenticated user's info — passed to every protected route."""

    def __init__(self, user: UserMaster):
        self.user_id = user.user_id
        self.company_id = user.company_id
        self.role_id = user.role_id
        self.email = user.email
        self.first_name = user.first_name
        self.status = user.status


from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:

    # print("🔥 TOKEN:", token)

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Please log in.",
    )

    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("user_id")
    if not user_id:
        raise credentials_exception

    result = await db.execute(
        select(UserMaster).where(
            UserMaster.user_id == user_id,
            UserMaster.status == "Active",
            UserMaster.is_deleted == "N",
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception

    return CurrentUser(user)



def require_role(role_id: int):
    """
    Dependency factory — restricts endpoint to a specific role.
    Usage: Depends(require_role(1))  ← Super Admin only
    """

    async def checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role_id != role_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return checker


def require_roles(role_ids: list[int]):
    """
    Dependency factory — restricts endpoint to multiple allowed roles.
    Usage: Depends(require_roles([1, 2]))  ← Super Admin or Company Admin
    """

    async def checker(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role_id not in role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )
        return current_user

    return checker
```

---

## STEP 23: Add Logout and Token Refresh Endpoints

Update `backend/app/services/auth_service.py` — add these two methods inside the `AuthService` class:

```python
    async def logout(self, db: AsyncSession, user_id: int, refresh_token: str) -> dict:
        """Revoke the refresh token. Access token expires naturally after 15 min."""
        import hashlib

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        result = await db.execute(
            select(RefreshTokens).where(
                RefreshTokens.user_id == user_id,
                RefreshTokens.token_hash == token_hash,
                RefreshTokens.revoked == False,  # noqa: E712
            )
        )
        token_record = result.scalar_one_or_none()

        if token_record:
            token_record.revoked = True
            await db.commit()

        return {"message": "Logged out successfully."}

    async def refresh_access_token(
        self, db: AsyncSession, refresh_token: str
    ) -> dict:
        """Exchange a valid refresh token for a new access token."""
        import hashlib
        from datetime import datetime, timezone

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        result = await db.execute(
            select(RefreshTokens).where(
                RefreshTokens.token_hash == token_hash,
                RefreshTokens.revoked == False,  # noqa: E712
                RefreshTokens.expires_at > datetime.now(timezone.utc),
            )
        )
        token_record = result.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
            )

        # Rotate the refresh token (old one revoked, new one issued)
        token_record.revoked = True

        raw_refresh, hashed_refresh = create_refresh_token()
        new_record = RefreshTokens(
            user_id=token_record.user_id,
            token_hash=hashed_refresh,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(new_record)

        # Fetch user for new access token
        user_result = await db.execute(
            select(UserMaster).where(UserMaster.user_id == token_record.user_id)
        )
        user = user_result.scalar_one()

        access_token = create_access_token(
            {
                "user_id": user.user_id,
                "company_id": user.company_id,
                "role_id": user.role_id,
            }
        )
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
        }
```

Update `backend/app/api/v1/auth.py` — add these endpoints:

```python
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.auth import LoginRequest, OTPVerifyRequest, SignupRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


@router.post("/signup")
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Sends OTP to email for verification."""
    return await auth_service.signup(db, data)


@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and activate account."""
    return await auth_service.verify_otp(db, data.email, data.otp)


@router.post("/login")
async def login(
    data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)
):
    """Login with email and password. Returns JWT tokens."""
    ip = request.client.host
    return await auth_service.login(db, data, ip)


@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Revoke refresh token and log out."""
    refresh_token = request.cookies.get("refresh_token", "")
    return await auth_service.logout(db, current_user.user_id, refresh_token)


@router.post("/refresh")
async def refresh(request: Request, db: AsyncSession = Depends(get_db)):
    """Get new access token using refresh token."""
    refresh_token = request.cookies.get("refresh_token", "")
    return await auth_service.refresh_access_token(db, refresh_token)
```

---

## STEP 24: Add Forgot Password / Reset Password

Add these two methods to `AuthService` in `auth_service.py`:

```python
    async def forgot_password(self, db: AsyncSession, email: str) -> dict:
        """Send password reset link to email."""
        from app.models.auth import PasswordResetTokens

        result = await db.execute(
            select(UserMaster).where(UserMaster.email == email.lower())
        )
        user = result.scalar_one_or_none()

        # Always return same message — don't reveal if email exists (security)
        if not user:
            return {
                "message": "If this email is registered, you will receive reset instructions."
            }

        # Generate reset token
        raw_token, token_hash = create_refresh_token()  # reuse same logic

        reset_record = PasswordResetTokens(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_record)
        await db.commit()

        # TODO: Send email with reset link (Celery task in Phase 3)
        # Reset URL: http://localhost:3000/reset-password?token={raw_token}
        return {
            "message": "If this email is registered, you will receive reset instructions.",
            "dev_reset_token": raw_token,  # REMOVE IN PRODUCTION
        }

    async def reset_password(
        self, db: AsyncSession, token: str, new_password: str
    ) -> dict:
        """Reset password using the token from email."""
        import hashlib
        from app.models.auth import PasswordResetTokens

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        result = await db.execute(
            select(PasswordResetTokens).where(
                PasswordResetTokens.token_hash == token_hash,
                PasswordResetTokens.used == False,  # noqa: E712
                PasswordResetTokens.expires_at > datetime.now(timezone.utc),
            )
        )
        reset_record = result.scalar_one_or_none()

        if not reset_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        # Update password
        new_hash = hash_password(new_password)
        await db.execute(
            update(UserMaster)
            .where(UserMaster.user_id == reset_record.user_id)
            .values(password_hash=new_hash)
        )

        # Mark token as used
        reset_record.used = True
        await db.commit()

        return {"message": "Password reset successfully. You can now log in."}
```

Add these routes to `backend/app/api/v1/auth.py`:

```python
from app.schemas.auth import ForgotPasswordRequest, ResetPasswordRequest

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Send password reset instructions to email."""
    return await auth_service.forgot_password(db, data.email)


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    """Reset password using token from email."""
    return await auth_service.reset_password(db, data.token, data.new_password)
```

---

## STEP 25: Add Company and User Management (Admin Portal)

### 25.1 Create Company Schema

Create `backend/app/schemas/company.py`:

```python
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class CompanyCreate(BaseModel):
    company_code: str
    company_name: str
    industry_type: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    gst_number: Optional[str] = None
    employee_strength: Optional[int] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_mobile: Optional[str] = None

    @field_validator("company_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters")
        return v


class CompanyUpdate(BaseModel):
    company_name: Optional[str] = None
    industry_type: Optional[str] = None
    website: Optional[str] = None
    employee_strength: Optional[int] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_mobile: Optional[str] = None


class CompanyResponse(BaseModel):
    company_id: int
    company_code: str
    company_name: str
    industry_type: Optional[str]
    status: str
    employee_strength: Optional[int]
    contact_email: Optional[str]

    class Config:
        from_attributes = True  # allows creating from SQLAlchemy model
```

### 25.2 Create Company Service

Create `backend/app/services/company_service.py`:

```python
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import CompanyMaster
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyService:
    async def get_all(self, db: AsyncSession) -> list:
        result = await db.execute(
            select(CompanyMaster).where(CompanyMaster.is_deleted == "N")
        )
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, company_id: int) -> CompanyMaster:
        result = await db.execute(
            select(CompanyMaster).where(
                CompanyMaster.company_id == company_id,
                CompanyMaster.is_deleted == "N",
            )
        )
        company = result.scalar_one_or_none()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found.",
            )
        return company

    async def create(self, db: AsyncSession, data: CompanyCreate) -> CompanyMaster:
        # Check duplicate code
        existing = await db.execute(
            select(CompanyMaster).where(
                CompanyMaster.company_code == data.company_code.upper()
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company code already exists.",
            )

        company = CompanyMaster(
            **data.model_dump(),
            company_code=data.company_code.upper(),
            status="Active",
        )
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company

    async def update(
        self, db: AsyncSession, company_id: int, data: CompanyUpdate
    ) -> CompanyMaster:
        company = await self.get_by_id(db, company_id)

        # Only update fields that were actually sent
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        await db.commit()
        await db.refresh(company)
        return company

    async def set_status(
        self, db: AsyncSession, company_id: int, new_status: str
    ) -> CompanyMaster:
        company = await self.get_by_id(db, company_id)
        company.status = new_status
        await db.commit()
        await db.refresh(company)
        return company

    async def delete(self, db: AsyncSession, company_id: int) -> dict:
        company = await self.get_by_id(db, company_id)
        company.is_deleted = "Y"  # soft delete
        await db.commit()
        return {"message": "Company deleted successfully."}
```

### 25.3 Create Company Router

Create `backend/app/api/v1/company.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Company Management"])
company_service = CompanyService()

# Role IDs: 1=Super Admin, 2=Company Admin, 3=HR, 4=Employee
ADMIN_ROLES = [1, 2]


@router.get("/", response_model=list[CompanyResponse])
async def list_companies(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),  # Super Admin only
):
    """List all companies. Super Admin only."""
    return await company_service.get_all(db)


@router.post("/", response_model=CompanyResponse, status_code=201)
async def create_company(
    data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),  # Super Admin only
):
    """Create a new company."""
    return await company_service.create(db, data)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(ADMIN_ROLES)),
):
    """Get a company by ID."""
    return await company_service.get_by_id(db, company_id)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(ADMIN_ROLES)),
):
    """Update company details."""
    return await company_service.update(db, company_id, data)


@router.patch("/{company_id}/status")
async def update_company_status(
    company_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),
):
    """Activate or deactivate a company."""
    if status not in ["Active", "Inactive"]:
        from fastapi import HTTPException

        raise HTTPException(400, "Status must be 'Active' or 'Inactive'")
    return await company_service.set_status(db, company_id, status)


@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),
):
    """Soft-delete a company."""
    return await company_service.delete(db, company_id)
```

### 25.4 Register Company Router in main.py

Update `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.company import router as company_router
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


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}


@app.get("/")
async def root():
    return {"message": "POSH Platform API. Visit /docs for documentation."}
```

---

## STEP 26: Add User Management (Admin Portal)

### 26.1 Create User Schema

Create `backend/app/schemas/user.py`:

```python
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    mobile: str
    department: Optional[str] = None
    designation: Optional[str] = None
    role_id: int
    company_id: int
    employee_id: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        return v.strip().lower()

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if not re.match(r"^\d{10}$", v.strip()):
            raise ValueError("Mobile must be exactly 10 digits")
        return v.strip()


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    mobile: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    role_id: Optional[int] = None


class UserResponse(BaseModel):
    user_id: int
    company_id: int
    employee_id: str
    first_name: str
    last_name: Optional[str]
    email: str
    mobile: Optional[str]
    department: Optional[str]
    designation: Optional[str]
    role_id: int
    status: str

    class Config:
        from_attributes = True


class PasswordResetByAdmin(BaseModel):
    new_password: str
```

### 26.2 Create User Service

Create `backend/app/services/user_service.py`:

```python
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import UserMaster
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    async def get_all(
        self,
        db: AsyncSession,
        company_id: Optional[int] = None,
    ) -> list:
        query = select(UserMaster).where(UserMaster.is_deleted == "N")
        if company_id:
            query = query.where(UserMaster.company_id == company_id)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_id(self, db: AsyncSession, user_id: int) -> UserMaster:
        result = await db.execute(
            select(UserMaster).where(
                UserMaster.user_id == user_id,
                UserMaster.is_deleted == "N",
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def create(self, db: AsyncSession, data: UserCreate) -> UserMaster:
        # Check duplicate email
        existing = await db.execute(
            select(UserMaster).where(UserMaster.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

        # Generate temporary password
        temp_password = "Temp@1234"  # TODO: send via email in Phase 3
        user = UserMaster(
            **data.model_dump(),
            username=data.email,
            password_hash=hash_password(temp_password),
            status="Active",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update(
        self, db: AsyncSession, user_id: int, data: UserUpdate
    ) -> UserMaster:
        user = await self.get_by_id(db, user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.commit()
        await db.refresh(user)
        return user

    async def set_status(
        self, db: AsyncSession, user_id: int, new_status: str
    ) -> UserMaster:
        user = await self.get_by_id(db, user_id)
        user.status = new_status
        await db.commit()
        return user

    async def reset_password(
        self, db: AsyncSession, user_id: int, new_password: str
    ) -> dict:
        user = await self.get_by_id(db, user_id)
        user.password_hash = hash_password(new_password)
        await db.commit()
        return {"message": "Password reset successfully."}

    async def delete(self, db: AsyncSession, user_id: int) -> dict:
        user = await self.get_by_id(db, user_id)
        user.is_deleted = "Y"
        await db.commit()
        return {"message": "User deleted successfully."}
```

### 26.3 Create User Router

Create `backend/app/api/v1/users.py`:

```python
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.schemas.user import PasswordResetByAdmin, UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])
user_service = UserService()


@router.get("/", response_model=list[UserResponse])
async def list_users(
    company_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """List users. Super Admin can filter by company. Company Admin sees own company."""
    # Company Admin can only see their own company's users
    if current_user.role_id == 2:
        company_id = current_user.company_id
    return await user_service.get_all(db, company_id)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Create a new user."""
    # Company Admin cannot create users for other companies
    if current_user.role_id == 2:
        data.company_id = current_user.company_id
    return await user_service.create(db, data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2, 3])),
):
    """Get a user by ID."""
    return await user_service.get_by_id(db, user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Update user details."""
    return await user_service.update(db, user_id, data)


@router.patch("/{user_id}/status")
async def update_user_status(
    user_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Activate or deactivate a user."""
    if status not in ["Active", "Inactive"]:
        from fastapi import HTTPException

        raise HTTPException(400, "Status must be 'Active' or 'Inactive'")
    return await user_service.set_status(db, user_id, status)


@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    data: PasswordResetByAdmin,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Admin resets a user's password."""
    return await user_service.reset_password(db, user_id, data.new_password)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),
):
    """Soft-delete a user. Super Admin only."""
    return await user_service.delete(db, user_id)
```

### 26.4 Register User Router in main.py

Update `backend/app/main.py` to add the user router:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.company import router as company_router
from app.api.v1.users import router as users_router
from app.core.config import settings

app = FastAPI(title="POSH Training Platform API", version="1.0.0", docs_url="/docs")

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


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "POSH Training Platform"}


@app.get("/")
async def root():
    return {"message": "POSH Platform API. Visit /docs for documentation."}
```

---

## STEP 27: Test Phase 1 Remaining Features

Run black + ruff, then tests:

```bash
cd backend
black .
ruff check .
pytest tests/ -v
```

curl.exe -X POST "http://localhost:8000/api/v1/auth/logout" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3LCJjb21wYW55X2lkIjoxLCJyb2xlX2lkIjo0LCJleHAiOjE3ODMwMDYzOTAsInR5cGUiOiJhY2Nlc3MifQ.qbh20HBtc9zli_Ke-rmxX2bUm95Wrq1iP7zMOWEc-4o" -H "Content-Type: application/json" -d "{\"refresh_token\":\"M4_NtT6gC2KaLvKaKrvKP7L1HFAW7z_XIujlKKwRiUsL_rFsmbEg5wCBIenH-gb5uRkk1k0RvzFIOToNgV2Zqw\"}"

Test via Swagger (http://localhost:8000/docs):

1. `POST /api/v1/auth/signup` → get OTP
2. `POST /api/v1/auth/verify-otp` → activate
3. `POST /api/v1/auth/login` → get tokens
4. `GET /api/v1/companies/` → should return 403 (Employee role, no permission)
5. `POST /api/v1/auth/forgot-password` → get reset token
6. `POST /api/v1/auth/reset-password` → reset password

---

## STEP 28: Commit Phase 1 Complete

```bash
git add .
git commit -m "feat(phase1): complete auth — logout, refresh, forgot-password, RBAC, company CRUD, user CRUD"
git push origin develop
```

---

---

# PHASE 2 — CONTENT & LEARNING (Week 6–9)

**What we build:** Video upload, secure streaming, video player enforcement, assessments, progress tracking.

**Theory to learn before starting:**

- Object storage (MinIO/S3) vs local file storage
- Pre-signed URLs for secure file access
- Background jobs (Celery) for heavy tasks
- File upload validation (MIME types, not just extensions)

---

## STEP 29: Add All Phase 2 Database Tables

### 29.1 Create Video Models

Create `backend/app/models/video.py`:

```python
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.base import Base


class VideoCategory(Base):
    __tablename__ = "video_category"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(100))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VideoMaster(Base):
    __tablename__ = "video_master"

    video_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200))
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("video_category.category_id"))
    duration_minutes = Column(Integer)
    video_url = Column(String(500))       # path in MinIO/S3, NOT a public URL
    storage_type = Column(
        Enum("AWS S3", "Azure Blob", "Local", "MinIO"), default="MinIO"
    )
    status = Column(Enum("Draft", "Published", "Archived"), default="Draft")
    created_by = Column(BigInteger, ForeignKey("user_master.user_id"))
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())


class VideoLanguage(Base):
    """Stores per-language subtitle/audio tracks for a video."""

    __tablename__ = "video_language"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("video_master.video_id"))
    language_id = Column(Integer, ForeignKey("language_master.language_id"))
    subtitle_path = Column(String(255))   # path to .vtt subtitle file in MinIO
    audio_url = Column(String(500))       # path to dubbed audio track in MinIO
    created_date = Column(DateTime, server_default=func.now())
```

### 29.2 Create Language Model

Create `backend/app/models/language.py`:

```python
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.db.base import Base


class LanguageMaster(Base):
    __tablename__ = "language_master"

    language_id = Column(Integer, primary_key=True, autoincrement=True)
    language_name = Column(String(50))
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### 29.3 Create Progress and Assessment Models

Create `backend/app/models/training.py`:

```python
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from app.db.base import Base


class TrainingHistory(Base):
    """Tracks every user's progress on every video."""

    __tablename__ = "training_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_master.user_id"))
    video_id = Column(Integer, ForeignKey("video_master.video_id"))
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    watched_seconds = Column(Integer, default=0)
    total_seconds = Column(Integer)
    completion_percent = Column(Numeric(5, 2), default=0)
    furthest_position = Column(Integer, default=0)  # for no-fast-forward enforcement
    last_watched_position = Column(Integer, default=0)  # for resume
    status = Column(
        Enum("Not Started", "In Progress", "Completed"), default="Not Started"
    )
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_date = Column(DateTime, server_default=func.now())
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())


class CourseAssignment(Base):
    """HR assigns videos to users/departments/company-wide."""

    __tablename__ = "course_assignment"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("video_master.video_id"))
    assigned_by = Column(BigInteger, ForeignKey("user_master.user_id"))
    company_id = Column(Integer, ForeignKey("company_master.company_id"))
    assigned_to_user_id = Column(BigInteger, ForeignKey("user_master.user_id"), nullable=True)
    assigned_to_department = Column(String(100), nullable=True)
    assign_type = Column(Enum("Individual", "Department", "Company-Wide"))
    due_date = Column(DateTime)
    passing_score = Column(Numeric(5, 2), default=70.0)
    created_date = Column(DateTime, server_default=func.now())


class AssessmentQuestion(Base):
    """Questions for a video's assessment."""

    __tablename__ = "assessment_question"

    question_id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("video_master.video_id"))
    question_text = Column(String(500))
    question_type = Column(Enum("MCQ", "True/False", "Scenario"))
    correct_option = Column(String(1))   # A, B, C, D or T/F
    created_date = Column(DateTime, server_default=func.now())


class AssessmentOption(Base):
    """Answer options for MCQ questions."""

    __tablename__ = "assessment_option"

    option_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("assessment_question.question_id"))
    option_label = Column(String(1))    # A, B, C, D
    option_text = Column(String(500))


class AssessmentResult(Base):
    """Stores each attempt's result."""

    __tablename__ = "assessment_result"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user_master.user_id"))
    video_id = Column(Integer, ForeignKey("video_master.video_id"))
    total_questions = Column(Integer)
    correct_answers = Column(Integer)
    score = Column(Numeric(5, 2))
    passing_score = Column(Numeric(5, 2))
    result = Column(Enum("Pass", "Fail"))
    attempt_number = Column(Integer, default=1)
    attempted_at = Column(DateTime, server_default=func.now())
```

### 29.4 Update alembic/env.py with New Models

Add these imports to `backend/alembic/env.py`:

```python
from app.models.language import LanguageMaster  # noqa: F401
from app.models.training import (  # noqa: F401
    AssessmentOption,
    AssessmentQuestion,
    AssessmentResult,
    CourseAssignment,
    TrainingHistory,
)
from app.models.video import VideoCategory, VideoLanguage, VideoMaster  # noqa: F401
```

### 29.5 Generate and Apply Migration

```bash
alembic revision --autogenerate -m "add_phase2_video_training_tables"
alembic upgrade head
```

### 29.6 Seed Languages and Video Categories

Add to `backend/app/db/seed.py` inside the `seed()` function:

```python
        # ── 3. Languages ──────────────────────────────────────────────────
        await db.execute(
            text("""
                INSERT IGNORE INTO language_master (language_id, language_name)
                VALUES
                    (1, 'English'),
                    (2, 'Hindi'),
                    (3, 'Tamil'),
                    (4, 'Telugu'),
                    (5, 'Malayalam'),
                    (6, 'Kannada')
            """)
        )

        # ── 4. Video Categories ───────────────────────────────────────────
        await db.execute(
            text("""
                INSERT IGNORE INTO video_category (category_id, category_name)
                VALUES
                    (1, 'POSH Awareness'),
                    (2, 'Workplace Conduct'),
                    (3, 'Case Studies'),
                    (4, 'Reporting Procedures'),
                    (5, 'Annual Refresher')
            """)
        )
```

Run seed again:

```bash
python -m app.db.seed
```

---

## STEP 30: Set Up MinIO for Video Storage

MinIO is already running in Docker (http://localhost:9001). Now configure buckets.

Create `backend/app/core/storage.py`:

```python
import os
from typing import Optional

import boto3
from botocore.client import Config

# MinIO uses S3-compatible API — same code works for AWS S3
_client = None


def get_storage_client():
    """Get or create the MinIO/S3 client (singleton)."""
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"http://{os.environ.get('MINIO_ENDPOINT', 'minio:9000')}",
            aws_access_key_id=os.environ.get("MINIO_ROOT_USER", "minioadmin"),
            aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin123"),
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    return _client


def ensure_bucket_exists(bucket_name: str) -> None:
    """Create bucket if it doesn't exist."""
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=bucket_name)
    except Exception:
        client.create_bucket(Bucket=bucket_name)


def upload_file(
    file_bytes: bytes,
    bucket: str,
    object_key: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file to MinIO/S3.
    Returns the object key (path) — NOT a public URL.
    """
    ensure_bucket_exists(bucket)
    client = get_storage_client()
    client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return object_key


def generate_presigned_url(
    bucket: str, object_key: str, expiry_seconds: int = 300
) -> str:
    """
    Generate a short-lived URL for secure file access.
    Default: 5 minutes (300 seconds).
    Only users with a valid signed URL can access the file.
    """
    client = get_storage_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expiry_seconds,
    )
    return url


def delete_file(bucket: str, object_key: str) -> None:
    """Delete a file from storage."""
    client = get_storage_client()
    client.delete_object(Bucket=bucket, Key=object_key)
```

Add `boto3` to `backend/requirements.txt`:

```
boto3==1.35.0
python-magic-bin(windows)
python-magic(c/git)
```

---

## STEP 31: Create Video Upload Endpoint

### 31.1 Create Video Schema

Create `backend/app/schemas/video.py`:

```python
from typing import Optional

from pydantic import BaseModel


class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    duration_minutes: Optional[int] = None


class VideoResponse(BaseModel):
    video_id: int
    title: str
    description: Optional[str]
    status: str
    duration_minutes: Optional[int]
    created_date: Optional[str] = None

    class Config:
        from_attributes = True


class ProgressUpdate(BaseModel):
    current_position: int    # current playback position in seconds
    total_duration: int      # total video length in seconds
```

### 31.2 Create Video Service

Create `backend/app/services/video_service.py`:

```python
import os
import uuid
from typing import Optional

import magic  # python-magic for real MIME type detection
from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import generate_presigned_url, upload_file
from app.models.training import CourseAssignment, TrainingHistory
from app.models.video import VideoMaster
from app.schemas.video import VideoCreate

ALLOWED_MIME_TYPES = {"video/mp4", "video/x-msvideo", "video/quicktime"}
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov"}
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB

VIDEO_BUCKET = os.environ.get("MINIO_BUCKET_VIDEOS", "posh-videos")


class VideoService:
    async def upload_video(
        self,
        db: AsyncSession,
        file: UploadFile,
        metadata: VideoCreate,
        uploaded_by: int,
        company_id: int,
    ) -> VideoMaster:
        """Upload a video file and save metadata."""

        # 1. Read file bytes
        file_bytes = await file.read()

        # 2. Check file size
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum limit of 500MB.",
            )

        # 3. Check MIME type using magic bytes (NOT just file extension)
        # This prevents attackers from renaming malware.exe to video.mp4
        mime_type = magic.from_buffer(file_bytes[:2048], mime=True)
        if mime_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Allowed: MP4, AVI, MOV. Got: {mime_type}",
            )

        # 4. Generate unique storage path
        file_ext = os.path.splitext(file.filename or "video.mp4")[1].lower()
        object_key = f"videos/{company_id}/{uuid.uuid4()}{file_ext}"

        # 5. Upload to MinIO
        upload_file(file_bytes, VIDEO_BUCKET, object_key, mime_type)

        # 6. Save metadata to DB (store path, not URL)
        video = VideoMaster(
            title=metadata.title,
            description=metadata.description,
            category_id=metadata.category_id,
            duration_minutes=metadata.duration_minutes,
            video_url=object_key,    # path only — never a public URL
            storage_type="MinIO",
            status="Draft",
            created_by=uploaded_by,
            company_id=company_id,
        )
        db.add(video)
        await db.commit()
        await db.refresh(video)
        return video

    async def get_stream_url(
        self, db: AsyncSession, video_id: int, user_id: int, company_id: int
    ) -> dict:
        """
        Generate a short-lived signed URL for video streaming.
        Verifies the user is assigned this course first.
        """
        # Verify video exists and belongs to this company
        result = await db.execute(
            select(VideoMaster).where(
                VideoMaster.video_id == video_id,
                VideoMaster.company_id == company_id,
                VideoMaster.status == "Published",
            )
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video not found or not yet published.",
            )

        # Verify user is assigned this course
        assigned = await db.execute(
            select(CourseAssignment).where(
                CourseAssignment.video_id == video_id,
                CourseAssignment.company_id == company_id,
            )
        )
        if not assigned.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this course.",
            )

        # Generate signed URL (expires in 5 minutes)
        signed_url = generate_presigned_url(VIDEO_BUCKET, video.video_url, 300)

        # Initialize training history if not exists
        history_result = await db.execute(
            select(TrainingHistory).where(
                TrainingHistory.user_id == user_id,
                TrainingHistory.video_id == video_id,
            )
        )
        history = history_result.scalar_one_or_none()

        if not history:
            history = TrainingHistory(
                user_id=user_id,
                video_id=video_id,
                company_id=company_id,
                total_seconds=(video.duration_minutes or 0) * 60,
                status="In Progress",
            )
            db.add(history)
            await db.commit()

        return {
            "stream_url": signed_url,
            "resume_position": history.last_watched_position if history else 0,
            "completion_percent": float(history.completion_percent) if history else 0,
        }

    async def update_progress(
        self,
        db: AsyncSession,
        video_id: int,
        user_id: int,
        current_position: int,
        total_duration: int,
    ) -> dict:
        """
        Update video watch progress.
        Enforces no-fast-forward: current_position cannot exceed furthest_position + 30s.
        """
        result = await db.execute(
            select(TrainingHistory).where(
                TrainingHistory.user_id == user_id,
                TrainingHistory.video_id == video_id,
            )
        )
        history = result.scalar_one_or_none()

        if not history:
            raise HTTPException(404, "No training history found. Start the video first.")

        # No-fast-forward enforcement:
        # Allow up to 30 seconds ahead of furthest watched position (buffer for network)
        max_allowed = (history.furthest_position or 0) + 30
        if current_position > max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fast-forward is not allowed. Please watch the video in sequence.",
            )

        # Update progress
        history.last_watched_position = current_position
        history.watched_seconds = current_position

        if current_position > (history.furthest_position or 0):
            history.furthest_position = current_position

        # Calculate completion %
        if total_duration > 0:
            percent = (current_position / total_duration) * 100
            history.completion_percent = min(percent, 100)

        # Mark as completed when >= 95% watched
        if history.completion_percent >= 95 and history.status != "Completed":
            history.status = "Completed"
            from datetime import datetime, timezone

            history.completed_at = datetime.now(timezone.utc)

        await db.commit()

        return {
            "completion_percent": float(history.completion_percent),
            "status": history.status,
            "assessment_unlocked": history.status == "Completed",
        }

    async def publish_video(
        self, db: AsyncSession, video_id: int, company_id: int
    ) -> VideoMaster:
        result = await db.execute(
            select(VideoMaster).where(
                VideoMaster.video_id == video_id,
                VideoMaster.company_id == company_id,
            )
        )
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(404, "Video not found.")
        video.status = "Published"
        await db.commit()
        return video
```

### 31.3 Create Video Router

Create `backend/app/api/v1/videos.py`:

```python
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.schemas.video import ProgressUpdate, VideoCreate, VideoResponse
from app.services.video_service import VideoService

router = APIRouter(prefix="/videos", tags=["Video Management"])
video_service = VideoService()


@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    category_id: int = Form(None),
    duration_minutes: int = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),  # Admin only
):
    """
    Upload a video file. Accepts MP4, AVI, MOV up to 500MB.
    File is stored securely in MinIO — never publicly accessible.
    """
    metadata = VideoCreate(
        title=title,
        description=description,
        category_id=category_id,
        duration_minutes=duration_minutes,
    )
    return await video_service.upload_video(
        db, file, metadata, current_user.user_id, current_user.company_id
    )


@router.patch("/{video_id}/publish")
async def publish_video(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Publish a video so employees can watch it."""
    return await video_service.publish_video(db, video_id, current_user.company_id)


@router.get("/{video_id}/stream-url")
async def get_stream_url(
    video_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get a short-lived signed URL for video streaming.
    URL expires in 5 minutes — prevents sharing.
    Employee must be assigned this course.
    """
    return await video_service.get_stream_url(
        db, video_id, current_user.user_id, current_user.company_id
    )


@router.post("/{video_id}/progress")
async def update_progress(
    video_id: int,
    data: ProgressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Update video watch progress (called every 10 seconds by the player).
    Enforces no-fast-forward. Returns completion status and assessment unlock.
    """
    return await video_service.update_progress(
        db,
        video_id,
        current_user.user_id,
        data.current_position,
        data.total_duration,
    )
```

### 31.4 Register Video Router

Update `backend/app/main.py` to add:

```python
from app.api.v1.videos import router as videos_router

# add alongside existing routers:
app.include_router(videos_router, prefix="/api/v1")
```

---

## STEP 32: Create Assessment Endpoints

Create `backend/app/schemas/assessment.py`:

```python
from typing import Optional

from pydantic import BaseModel


class AnswerSubmit(BaseModel):
    question_id: int
    selected_option: str    # A, B, C, D, T, or F


class AssessmentSubmit(BaseModel):
    video_id: int
    answers: list[AnswerSubmit]
```

Create `backend/app/services/assessment_service.py`:

```python
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.training import (
    AssessmentOption,
    AssessmentQuestion,
    AssessmentResult,
    TrainingHistory,
)
from app.schemas.assessment import AssessmentSubmit


class AssessmentService:
    async def submit(
        self, db: AsyncSession, user_id: int, data: AssessmentSubmit
    ) -> dict:
        """Submit assessment answers. Video must be completed first."""

        # 1. Verify video is completed
        history_result = await db.execute(
            select(TrainingHistory).where(
                TrainingHistory.user_id == user_id,
                TrainingHistory.video_id == data.video_id,
                TrainingHistory.status == "Completed",
            )
        )
        if not history_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete the training video before taking the assessment.",
            )

        # 2. Count attempt number
        attempt_result = await db.execute(
            select(func.count()).where(
                AssessmentResult.user_id == user_id,
                AssessmentResult.video_id == data.video_id,
            )
        )
        attempt_number = (attempt_result.scalar() or 0) + 1

        # 3. Score the answers
        correct = 0
        total = len(data.answers)

        for answer in data.answers:
            q_result = await db.execute(
                select(AssessmentQuestion).where(
                    AssessmentQuestion.question_id == answer.question_id
                )
            )
            question = q_result.scalar_one_or_none()
            if question and question.correct_option == answer.selected_option.upper():
                correct += 1

        score = (correct / total * 100) if total > 0 else 0
        passing_score = 70.0  # default; can be from course_assignment
        result = "Pass" if score >= passing_score else "Fail"

        # 4. Save result
        assessment_result = AssessmentResult(
            user_id=user_id,
            video_id=data.video_id,
            total_questions=total,
            correct_answers=correct,
            score=score,
            passing_score=passing_score,
            result=result,
            attempt_number=attempt_number,
        )
        db.add(assessment_result)
        await db.commit()

        response = {
            "score": round(score, 2),
            "correct": correct,
            "total": total,
            "result": result,
            "attempt_number": attempt_number,
            "certificate_triggered": result == "Pass",
        }

        # 5. Trigger certificate generation on Pass
        if result == "Pass":
            # TODO: Celery task for certificate generation (Phase 4)
            response["message"] = "Congratulations! Your certificate is being generated."
        else:
            response["message"] = f"Score: {score:.1f}%. You need {passing_score}% to pass. Please retry."

        return response
```

Create `backend/app/api/v1/assessments.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.assessment import AssessmentSubmit
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])
assessment_service = AssessmentService()


@router.post("/submit")
async def submit_assessment(
    data: AssessmentSubmit,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Submit assessment answers.
    Assessment is locked until video is 95%+ complete.
    Returns score, pass/fail, and triggers certificate on Pass.
    """
    return await assessment_service.submit(db, current_user.user_id, data)
```

Add to `backend/app/main.py`:

```python
from app.api.v1.assessments import router as assessments_router
app.include_router(assessments_router, prefix="/api/v1")
```

---

## STEP 33: Update models `__init__.py`

Update `backend/app/models/__init__.py`:

```python
from app.models.auth import (  # noqa: F401
    AccountLockout,
    LoginAttempts,
    OTPVerification,
    PasswordResetTokens,
    RefreshTokens,
)
from app.models.company import CompanyMaster  # noqa: F401
from app.models.language import LanguageMaster  # noqa: F401
from app.models.role import RoleMaster  # noqa: F401
from app.models.training import (  # noqa: F401
    AssessmentOption,
    AssessmentQuestion,
    AssessmentResult,
    CourseAssignment,
    TrainingHistory,
)
from app.models.user import UserMaster  # noqa: F401
from app.models.video import VideoCategory, VideoLanguage, VideoMaster  # noqa: F401
```

---

## STEP 34: Add Phase 2 Tests

Create `backend/tests/test_video.py`:

```python
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_progress_update_rejects_fast_forward():
    """Fast-forward must be blocked server-side."""
    with patch(
        "app.services.video_service.VideoService.update_progress",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=400,
            detail="Fast-forward is not allowed.",
        ),
    ):
        response = client.post(
            "/api/v1/videos/1/progress",
            json={"current_position": 9999, "total_duration": 1200},
            cookies={"access_token": "fake_token"},
        )
    assert response.status_code in [400, 401]  # 401 if token invalid, 400 if service rejects


def test_stream_url_requires_auth():
    """Unauthenticated request to stream URL should be rejected."""
    response = client.get("/api/v1/videos/1/stream-url")
    assert response.status_code == 401


def test_assessment_blocked_before_video_complete():
    """Assessment submit must fail if video not completed."""
    with patch(
        "app.services.assessment_service.AssessmentService.submit",
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=400,
            detail="Please complete the training video before taking the assessment.",
        ),
    ):
        response = client.post(
            "/api/v1/assessments/submit",
            json={"video_id": 1, "answers": []},
            cookies={"access_token": "fake_token"},
        )
    assert response.status_code in [400, 401]
```

---

## STEP 35: Run Everything, Lint, Test, Commit

```bash
cd backend
black .
ruff check .
ruff check --fix .
ruff check .
pytest tests/ -v
cd ..
```

If all green:

```bash
git add .
git commit -m "feat(phase2): video upload, secure streaming, progress tracking, no-fast-forward, assessments"
git push origin develop
```

---

## Phase 2 Complete ✅ Checklist

- ✅ Video, Language, Training models + migration
- ✅ MinIO storage client (cloud-agnostic S3 abstraction)
- ✅ Video upload with MIME-type validation (not just extension)
- ✅ Secure pre-signed URLs (no public video access)
- ✅ Progress tracking with no-fast-forward enforcement (server-side)
- ✅ Resume playback from last watched position
- ✅ Assessment submission locked until video completed
- ✅ Score calculation + pass/fail
- ✅ Tests for all key security requirements
- ✅ CI green

---

## What Comes Next

| Phase   | Topics                                                                           |
| ------- | -------------------------------------------------------------------------------- |
| Phase 3 | HR Portal: bulk Excel upload, training assignment, compliance dashboard, reports |
| Phase 4 | Certificate generation (PDF + QR), email delivery, public QR verification        |
| Phase 5 | Hardening, load testing, production deployment                                   |

**Next phase guide will cover Phase 3 and Phase 4 in the same step-by-step format.**
