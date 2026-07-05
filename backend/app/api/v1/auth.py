from fastapi import APIRouter, Depends, Request, Response
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    OTPVerifyRequest,
    ResetPasswordRequest,
    SignupRequest,
)
from app.services.auth_service import AuthService

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthService()


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.APP_ENV.lower() == "production",
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post("/signup")
@limiter.limit("5/minute")
async def signup(request: Request, data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. Sends OTP to email for verification."""
    return await auth_service.signup(db, data)


@router.post("/verify-otp")
async def verify_otp(data: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and activate account."""
    return await auth_service.verify_otp(db, data.email, data.otp)


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password. Returns JWT tokens."""
    ip = request.client.host
    result = await auth_service.login(db, data, ip)
    _set_refresh_cookie(response, result["refresh_token"])
    return result


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Revoke refresh token and log out."""
    refresh_token = request.cookies.get("refresh_token", "")
    result = await auth_service.logout(db, current_user.user_id, refresh_token)
    response.delete_cookie("refresh_token", path="/api/v1/auth")
    return result


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """Get new access token using refresh token."""
    refresh_token = request.cookies.get("refresh_token", "")
    result = await auth_service.refresh_access_token(db, refresh_token)
    _set_refresh_cookie(response, result["refresh_token"])
    return result


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset instructions to email."""
    return await auth_service.forgot_password(db, data.email)


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from email."""
    return await auth_service.reset_password(db, data.token, data.new_password)


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Authenticated user changes their own password."""
    return await auth_service.change_password(
        db, current_user.user_id, data.current_password, data.new_password
    )
