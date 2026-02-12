"""
PresenceOS - User & Workspace Schemas
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str | None = None


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = None


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    avatar_url: str | None = None
    is_active: bool
    is_verified: bool
    oauth_provider: str | None = None
    created_at: datetime


# Workspace schemas
class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    timezone: str = "Europe/Paris"
    default_language: str = "fr"


class WorkspaceCreate(WorkspaceBase):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    logo_url: str | None = None
    timezone: str | None = None
    default_language: str | None = None


class WorkspaceResponse(WorkspaceBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    logo_url: str | None = None
    billing_plan: str
    created_at: datetime


class WorkspaceMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    workspace_id: UUID
    role: str
    user: UserResponse
    created_at: datetime


# Auth responses
class LoginResponse(BaseModel):
    user: UserResponse
    token: Token
    workspaces: list[WorkspaceResponse]
