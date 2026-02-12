"""
PresenceOS - User Endpoints
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession
from app.core.security import get_password_hash, verify_password
from app.models.user import WorkspaceMember
from app.schemas.user import UserResponse, UserUpdate, WorkspaceResponse
from pydantic import BaseModel

router = APIRouter()


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Get current user profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user: CurrentUser, db: DBSession):
    """Update current user profile."""
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/me/change-password")
async def change_password(
    data: ChangePasswordRequest, current_user: CurrentUser, db: DBSession
):
    """Change current user password."""
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth-only accounts",
        )

    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = get_password_hash(data.new_password)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.get("/me/workspaces", response_model=list[WorkspaceResponse])
async def get_my_workspaces(current_user: CurrentUser, db: DBSession):
    """Get all workspaces the current user belongs to."""
    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.workspace))
        .where(WorkspaceMember.user_id == current_user.id)
    )
    memberships = result.scalars().all()

    return [
        WorkspaceResponse.model_validate(m.workspace)
        for m in memberships
    ]
