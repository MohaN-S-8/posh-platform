import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_otp,
    hash_password,
    verify_password,
)
from app.models.auth import AccountLockout, LoginAttempts, OTPVerification, RefreshTokens
from app.models.user import UserMaster
from app.schemas.auth import LoginRequest, SignupRequest

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


class AuthService:
    async def signup(self, db: AsyncSession, data: SignupRequest) -> dict:
        # Check duplicate email
        result = await db.execute(select(UserMaster).where(UserMaster.email == data.email.lower()))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        password_hash = hash_password(data.password)

        user = UserMaster(
            company_id=1,
            employee_id=f"EMP{data.mobile}",
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email.lower(),
            mobile=data.mobile,
            role_id=4,
            username=data.email.lower(),
            password_hash=password_hash,
            status="Inactive",
        )
        db.add(user)
        await db.flush()

        raw_otp, otp_hash = generate_otp()

        otp_record = OTPVerification(
            email=data.email.lower(),
            otp_hash=otp_hash,
            purpose="Signup",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        db.add(otp_record)
        await db.commit()

        return {
            "message": "OTP sent to your email. Please verify to complete registration.",
            "dev_otp": raw_otp,  # REMOVE IN PRODUCTION
        }

    async def verify_otp(self, db: AsyncSession, email: str, otp: str) -> dict:
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()

        result = await db.execute(
            select(OTPVerification).where(
                OTPVerification.email == email.lower(),
                OTPVerification.otp_hash == otp_hash,
                OTPVerification.purpose == "Signup",
                OTPVerification.verified == False,  # noqa: E712
                OTPVerification.expires_at > datetime.now(timezone.utc),
            )
        )
        otp_record = result.scalar_one_or_none()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP.",
            )

        otp_record.verified = True
        await db.execute(
            update(UserMaster).where(UserMaster.email == email.lower()).values(status="Active")
        )
        await db.commit()
        return {"message": "Email verified successfully. You can now log in."}

    async def login(self, db: AsyncSession, data: LoginRequest, ip_address: str) -> dict:
        result = await db.execute(select(UserMaster).where(UserMaster.email == data.email.lower()))
        user = result.scalar_one_or_none()

        if not user:
            await self._log_attempt(db, None, data.email, ip_address, False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        lockout_result = await db.execute(
            select(AccountLockout).where(AccountLockout.user_id == user.user_id)
        )
        lockout = lockout_result.scalar_one_or_none()

        if lockout and lockout.locked_until and lockout.locked_until > datetime.now(timezone.utc):
            minutes_left = (
                int((lockout.locked_until - datetime.now(timezone.utc)).total_seconds() / 60) + 1
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked. Try again in {minutes_left} minutes.",
            )

        if not verify_password(data.password, user.password_hash):
            await self._log_attempt(db, user.user_id, data.email, ip_address, False)
            await self._increment_lockout(db, user.user_id, lockout)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if user.status != "Active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is inactive. Contact your administrator.",
            )

        if lockout:
            lockout.failed_attempts = 0
            lockout.locked_until = None

        access_token = create_access_token(
            {
                "user_id": user.user_id,
                "company_id": user.company_id,
                "role_id": user.role_id,
            }
        )
        raw_refresh, hashed_refresh = create_refresh_token()

        refresh_record = RefreshTokens(
            user_id=user.user_id,
            token_hash=hashed_refresh,
            ip_address=ip_address,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(refresh_record)
        await self._log_attempt(db, user.user_id, data.email, ip_address, True)
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": raw_refresh,
            "user_id": user.user_id,
            "role_id": user.role_id,
            "company_id": user.company_id,
        }

    async def _log_attempt(self, db, user_id, email, ip, success):
        attempt = LoginAttempts(
            user_id=user_id,
            email_attempted=email,
            ip_address=ip,
            success=success,
        )
        db.add(attempt)

    async def _increment_lockout(self, db, user_id, lockout):
        if not lockout:
            lockout = AccountLockout(user_id=user_id, failed_attempts=0)
            db.add(lockout)

        lockout.failed_attempts = (lockout.failed_attempts or 0) + 1

        if lockout.failed_attempts >= MAX_FAILED_ATTEMPTS:
            lockout.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
