"""
PresenceOS - Social Connectors Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.v1.deps import CurrentUser, DBSession, get_brand
from app.models.publishing import SocialConnector, SocialPlatform, ConnectorStatus
from app.schemas.publishing import (
    ConnectorCreate,
    ConnectorResponse,
    ConnectorListResponse,
    OAuthUrlRequest,
    OAuthUrlResponse,
    ApiKeyConnectRequest,
)
from app.connectors.factory import get_connector_handler

router = APIRouter()


@router.get("/brands/{brand_id}", response_model=list[ConnectorListResponse])
async def list_connectors(
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """List all social connectors for a brand."""
    await get_brand(brand_id, current_user, db)

    result = await db.execute(
        select(SocialConnector)
        .where(SocialConnector.brand_id == brand_id)
        .order_by(SocialConnector.platform)
    )
    connectors = result.scalars().all()

    return [ConnectorListResponse.model_validate(c) for c in connectors]


@router.post("/oauth/url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    data: OAuthUrlRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Generate OAuth URL for connecting a social platform."""
    await get_brand(data.brand_id, current_user, db)

    handler = get_connector_handler(data.platform)
    url, state = handler.get_oauth_url(str(data.brand_id))

    return OAuthUrlResponse(url=url, state=state)


@router.post("/oauth/callback", response_model=ConnectorResponse)
async def oauth_callback(
    data: ConnectorCreate,
    brand_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Handle OAuth callback and create connector."""
    await get_brand(brand_id, current_user, db)

    handler = get_connector_handler(data.platform)

    try:
        # Exchange code for tokens
        token_data = await handler.exchange_code(
            data.authorization_code,
            data.redirect_uri,
        )

        # Get account info
        account_info = await handler.get_account_info(token_data["access_token"])

        # Check if connector already exists for this account
        existing = await db.execute(
            select(SocialConnector).where(
                SocialConnector.brand_id == brand_id,
                SocialConnector.platform == data.platform,
                SocialConnector.account_id == account_info["account_id"],
            )
        )
        connector = existing.scalar_one_or_none()

        if connector:
            # Update existing connector
            connector.access_token_encrypted = handler.encrypt_token(
                token_data["access_token"]
            )
            if token_data.get("refresh_token"):
                connector.refresh_token_encrypted = handler.encrypt_token(
                    token_data["refresh_token"]
                )
            connector.token_expires_at = token_data.get("expires_at")
            connector.status = ConnectorStatus.CONNECTED
            connector.last_error = None
        else:
            # Create new connector
            connector = SocialConnector(
                brand_id=brand_id,
                platform=data.platform,
                account_id=account_info["account_id"],
                account_name=account_info.get("account_name"),
                account_username=account_info.get("account_username"),
                account_avatar_url=account_info.get("account_avatar_url"),
                access_token_encrypted=handler.encrypt_token(token_data["access_token"]),
                refresh_token_encrypted=(
                    handler.encrypt_token(token_data["refresh_token"])
                    if token_data.get("refresh_token")
                    else None
                ),
                token_expires_at=token_data.get("expires_at"),
                platform_data=account_info.get("platform_data"),
                scopes=token_data.get("scope"),
                status=ConnectorStatus.CONNECTED,
            )
            db.add(connector)

        await db.commit()
        await db.refresh(connector)

        return ConnectorResponse.model_validate(connector)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth failed: {str(e)}",
        )


@router.post("/api-key", response_model=ConnectorResponse)
async def connect_with_api_key(
    data: ApiKeyConnectRequest,
    current_user: CurrentUser,
    db: DBSession,
):
    """Connect a platform using an API key (Upload-Post)."""
    await get_brand(data.brand_id, current_user, db)

    handler = get_connector_handler(data.platform)

    # Get account info
    account_info = await handler.get_account_info(data.api_key)

    # Check if connector already exists
    existing = await db.execute(
        select(SocialConnector).where(
            SocialConnector.brand_id == data.brand_id,
            SocialConnector.platform == data.platform,
            SocialConnector.account_id == account_info["account_id"],
        )
    )
    connector = existing.scalar_one_or_none()

    if connector:
        connector.access_token_encrypted = handler.encrypt_token(data.api_key)
        connector.status = ConnectorStatus.CONNECTED
        connector.last_error = None
    else:
        connector = SocialConnector(
            brand_id=data.brand_id,
            platform=data.platform,
            account_id=account_info["account_id"],
            account_name=account_info.get("account_name"),
            account_username=account_info.get("account_username"),
            account_avatar_url=account_info.get("account_avatar_url"),
            access_token_encrypted=handler.encrypt_token(data.api_key),
            platform_data=account_info.get("platform_data"),
            status=ConnectorStatus.CONNECTED,
        )
        db.add(connector)

    await db.commit()
    await db.refresh(connector)

    return ConnectorResponse.model_validate(connector)


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_connector(
    connector_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Get connector details."""
    result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == connector_id)
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    await get_brand(connector.brand_id, current_user, db)

    return ConnectorResponse.model_validate(connector)


@router.post("/{connector_id}/refresh", response_model=ConnectorResponse)
async def refresh_connector_token(
    connector_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Refresh OAuth token for a connector."""
    result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == connector_id)
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    await get_brand(connector.brand_id, current_user, db)

    if not connector.refresh_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available. Please reconnect.",
        )

    handler = get_connector_handler(connector.platform)

    try:
        refresh_token = handler.decrypt_token(connector.refresh_token_encrypted)
        token_data = await handler.refresh_token(refresh_token)

        connector.access_token_encrypted = handler.encrypt_token(
            token_data["access_token"]
        )
        if token_data.get("refresh_token"):
            connector.refresh_token_encrypted = handler.encrypt_token(
                token_data["refresh_token"]
            )
        connector.token_expires_at = token_data.get("expires_at")
        connector.status = ConnectorStatus.CONNECTED
        connector.last_error = None

        await db.commit()
        await db.refresh(connector)

        return ConnectorResponse.model_validate(connector)

    except Exception as e:
        connector.status = ConnectorStatus.ERROR
        connector.last_error = str(e)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.delete("/{connector_id}")
async def disconnect_connector(
    connector_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Disconnect a social connector."""
    result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == connector_id)
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    await get_brand(connector.brand_id, current_user, db)

    # Try to revoke token with the platform (best effort)
    try:
        handler = get_connector_handler(connector.platform)
        access_token = handler.decrypt_token(connector.access_token_encrypted)
        await handler.revoke_token(access_token)
    except Exception:
        pass  # Ignore revocation failures

    # Mark as disconnected
    connector.status = ConnectorStatus.REVOKED
    connector.is_active = False
    await db.commit()

    return {"message": "Connector disconnected"}


@router.post("/{connector_id}/sync")
async def sync_connector_metrics(
    connector_id: UUID,
    current_user: CurrentUser,
    db: DBSession,
):
    """Manually trigger metrics sync for a connector."""
    result = await db.execute(
        select(SocialConnector).where(SocialConnector.id == connector_id)
    )
    connector = result.scalar_one_or_none()

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connector not found",
        )

    await get_brand(connector.brand_id, current_user, db)

    if connector.status != ConnectorStatus.CONNECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connector is not connected",
        )

    # TODO: Trigger async metrics sync job
    # from app.workers.tasks import sync_connector_metrics_task
    # sync_connector_metrics_task.delay(str(connector_id))

    return {"message": "Metrics sync initiated"}
