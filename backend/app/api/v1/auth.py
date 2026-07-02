from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

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
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Login with email and password. Returns JWT tokens."""
    ip = request.client.host
    return await auth_service.login(db, data, ip)
