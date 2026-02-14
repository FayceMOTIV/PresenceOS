"""
PresenceOS - Workspace Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CurrentUser, DBSession, get_current_workspace, get_workspace_admin
from app.models.user import Workspace, WorkspaceMember, UserRole, User
from app.models.brand import Brand
from app.schemas.user import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberResponse,
)
from app.schemas.brand import BrandListResponse
from pydantic import BaseModel, EmailStr

router = APIRouter()


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.MEMBER


@router.post("", response_model=WorkspaceResponse)
async def create_workspace(
    data: WorkspaceCreate, current_user: CurrentUser, db: DBSession
):
    """Create a new workspace."""
    # Check if slug is available
    result = await db.execute(select(Workspace).where(Workspace.slug == data.slug))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace slug already taken",
        )

    workspace = Workspace(**data.model_dump())
    db.add(workspace)
    await db.flush()

    # Add creator as owner
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=UserRole.OWNER,
    )
    db.add(member)

    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get workspace details."""
    workspace = await get_current_workspace(workspace_id, current_user, db)
    return WorkspaceResponse.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update workspace (admin only)."""
    workspace = await get_workspace_admin(workspace_id, current_user, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workspace, field, value)

    await db.commit()
    await db.refresh(workspace)

    return WorkspaceResponse.model_validate(workspace)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def get_workspace_members(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get all members of a workspace."""
    await get_current_workspace(workspace_id, current_user, db)

    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.user))
        .where(WorkspaceMember.workspace_id == workspace_id)
    )
    members = result.scalars().all()

    return [WorkspaceMemberResponse.model_validate(m) for m in members]


@router.post("/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def invite_member(
    workspace_id: UUID,
    data: InviteMemberRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Invite a user to the workspace (admin only)."""
    await get_workspace_admin(workspace_id, current_user, db)

    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. They must register first.",
        )

    # Check if already a member
    existing = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this workspace",
        )

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=data.role,
    )
    db.add(member)
    await db.commit()

    # Reload with user relationship
    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.user))
        .where(WorkspaceMember.id == member.id)
    )
    member = result.scalar_one()

    return WorkspaceMemberResponse.model_validate(member)


class UpdateMemberRoleRequest(BaseModel):
    role: UserRole


@router.patch("/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberResponse)
async def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    data: UpdateMemberRoleRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Update a member's role (admin only). Cannot change owner role."""
    await get_workspace_admin(workspace_id, current_user, db)

    result = await db.execute(
        select(WorkspaceMember)
        .options(selectinload(WorkspaceMember.user))
        .where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    if member.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the owner's role",
        )

    member.role = data.role
    await db.commit()
    await db.refresh(member, attribute_names=["user"])

    return WorkspaceMemberResponse.model_validate(member)


@router.delete("/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Remove a member from the workspace (admin only)."""
    await get_workspace_admin(workspace_id, current_user, db)

    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    if member.role == UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the workspace owner",
        )

    await db.delete(member)
    await db.commit()

    return {"message": "Member removed"}


@router.get("/{workspace_id}/brands", response_model=list[BrandListResponse])
async def get_workspace_brands(
    workspace_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get all brands in a workspace."""
    await get_current_workspace(workspace_id, current_user, db)

    result = await db.execute(
        select(Brand).where(Brand.workspace_id == workspace_id).order_by(Brand.name)
    )
    brands = result.scalars().all()

    return [BrandListResponse.model_validate(b) for b in brands]
