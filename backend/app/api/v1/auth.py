from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    OTPVerifyRequest,
    ResetPasswordRequest,
    SignupRequest,
)
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
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
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


@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send password reset instructions to email."""
    return await auth_service.forgot_password(db, data.email)


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using token from email."""
    return await auth_service.reset_password(db, data.token, data.new_password)
