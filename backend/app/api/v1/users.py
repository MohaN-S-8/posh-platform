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
    company_id = current_user.company_id if current_user.role_id in [2, 3] else None
    return await user_service.get_by_id(db, user_id, company_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Update user details."""
    company_id = current_user.company_id if current_user.role_id == 2 else None
    return await user_service.update(db, user_id, data, company_id)


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
    company_id = current_user.company_id if current_user.role_id == 2 else None
    return await user_service.set_status(db, user_id, status, company_id)


@router.post("/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    data: PasswordResetByAdmin,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1, 2])),
):
    """Admin resets a user's password."""
    company_id = current_user.company_id if current_user.role_id == 2 else None
    return await user_service.reset_password(db, user_id, data.new_password, company_id)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles([1])),
):
    """Soft-delete a user. Super Admin only."""
    return await user_service.delete(db, user_id)
