"""
PresenceOS - Pydantic Schemas
"""
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberResponse,
    Token,
    TokenPayload,
)
from app.schemas.brand import (
    BrandCreate,
    BrandUpdate,
    BrandResponse,
    BrandVoiceCreate,
    BrandVoiceUpdate,
    BrandVoiceResponse,
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItemResponse,
    KnowledgeImport,
)
from app.schemas.content import (
    ContentIdeaCreate,
    ContentIdeaUpdate,
    ContentIdeaResponse,
    ContentDraftCreate,
    ContentDraftUpdate,
    ContentDraftResponse,
    ContentVariantResponse,
    GenerateIdeasRequest,
    GenerateDraftRequest,
)
from app.schemas.publishing import (
    ConnectorCreate,
    ConnectorResponse,
    SchedulePostRequest,
    ScheduledPostResponse,
    PublishJobResponse,
    MetricsResponse,
)
from app.schemas.autopilot import (
    AutopilotConfigCreate,
    AutopilotConfigUpdate,
    AutopilotConfigResponse,
    PendingPostResponse,
    PendingPostAction,
)
from app.schemas.media import (
    MediaAssetResponse,
    MediaAssetUpdate,
    VoiceNoteResponse,
    MediaLibraryStats,
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceResponse",
    "WorkspaceMemberResponse",
    "Token",
    "TokenPayload",
    # Brand
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "BrandVoiceCreate",
    "BrandVoiceUpdate",
    "BrandVoiceResponse",
    "KnowledgeItemCreate",
    "KnowledgeItemUpdate",
    "KnowledgeItemResponse",
    "KnowledgeImport",
    # Content
    "ContentIdeaCreate",
    "ContentIdeaUpdate",
    "ContentIdeaResponse",
    "ContentDraftCreate",
    "ContentDraftUpdate",
    "ContentDraftResponse",
    "ContentVariantResponse",
    "GenerateIdeasRequest",
    "GenerateDraftRequest",
    # Publishing
    "ConnectorCreate",
    "ConnectorResponse",
    "SchedulePostRequest",
    "ScheduledPostResponse",
    "PublishJobResponse",
    "MetricsResponse",
    # Autopilot
    "AutopilotConfigCreate",
    "AutopilotConfigUpdate",
    "AutopilotConfigResponse",
    "PendingPostResponse",
    "PendingPostAction",
    # Media Library
    "MediaAssetResponse",
    "MediaAssetUpdate",
    "VoiceNoteResponse",
    "MediaLibraryStats",
]
