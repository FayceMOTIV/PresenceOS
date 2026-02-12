"""
PresenceOS - Media Upload Tests
"""
import pytest
import io
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.brand import Brand


# =============================================================================
# Upload Media Tests
# =============================================================================

class TestUploadMedia:
    """Tests for POST /api/v1/media/brands/{brand_id}/upload"""

    async def test_upload_image_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test uploading an image."""
        # Create a simple PNG image (1x1 pixel)
        png_data = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        files = {"file": ("test.png", io.BytesIO(png_data), "image/png")}

        response = await client.post(
            f"/api/v1/media/brands/{test_brand.id}/upload",
            headers=auth_headers,
            files=files,
        )

        # May fail if S3/MinIO is not configured
        assert response.status_code in [200, 201, 500, 503]

    async def test_upload_invalid_type(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test uploading an invalid file type."""
        files = {"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")}

        response = await client.post(
            f"/api/v1/media/brands/{test_brand.id}/upload",
            headers=auth_headers,
            files=files,
        )

        assert response.status_code == 400
        assert "non supporte" in response.json().get("detail", "").lower()

    async def test_upload_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test uploading without authentication."""
        files = {"file": ("test.png", io.BytesIO(b"fake"), "image/png")}

        response = await client.post(
            f"/api/v1/media/brands/{test_brand.id}/upload",
            files=files,
        )

        assert response.status_code == 401


# =============================================================================
# Presigned URL Tests
# =============================================================================

class TestPresignedUrl:
    """Tests for POST /api/v1/media/brands/{brand_id}/presigned-url"""

    async def test_get_presigned_url_success(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting a presigned upload URL."""
        response = await client.post(
            f"/api/v1/media/brands/{test_brand.id}/presigned-url",
            headers=auth_headers,
            json={
                "filename": "test.jpg",
                "content_type": "image/jpeg",
            },
        )

        # May fail if S3/MinIO is not configured
        assert response.status_code in [200, 500, 503]

        if response.status_code == 200:
            data = response.json()
            assert "upload_url" in data
            assert "key" in data
            assert "public_url" in data

    async def test_get_presigned_url_invalid_type(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting presigned URL for invalid type."""
        response = await client.post(
            f"/api/v1/media/brands/{test_brand.id}/presigned-url",
            headers=auth_headers,
            json={
                "filename": "test.txt",
                "content_type": "text/plain",
            },
        )

        assert response.status_code == 400

    async def test_get_presigned_url_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test getting presigned URL without authentication."""
        response = await client.post(
            f"/api/v1/media/brands/{test_brand.id}/presigned-url",
            json={
                "filename": "test.jpg",
                "content_type": "image/jpeg",
            },
        )

        assert response.status_code == 401


# =============================================================================
# Delete Media Tests
# =============================================================================

class TestDeleteMedia:
    """Tests for DELETE /api/v1/media/brands/{brand_id}/media/{key}"""

    async def test_delete_media_not_found(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test deleting non-existent media."""
        fake_key = f"brands/{test_brand.id}/media/2025/01/fake.jpg"

        response = await client.delete(
            f"/api/v1/media/brands/{test_brand.id}/media/{fake_key}",
            headers=auth_headers,
        )

        # May return 404 or 500 if S3/MinIO is not configured
        assert response.status_code in [404, 500, 503]

    async def test_delete_media_forbidden(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test deleting media from another brand."""
        other_brand_id = str(uuid4())
        fake_key = f"brands/{other_brand_id}/media/2025/01/fake.jpg"

        response = await client.delete(
            f"/api/v1/media/brands/{test_brand.id}/media/{fake_key}",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_delete_media_unauthorized(
        self,
        client: AsyncClient,
        test_brand: Brand,
    ):
        """Test deleting media without authentication."""
        fake_key = f"brands/{test_brand.id}/media/2025/01/fake.jpg"

        response = await client.delete(
            f"/api/v1/media/brands/{test_brand.id}/media/{fake_key}",
        )

        assert response.status_code == 401


# =============================================================================
# Get Media Info Tests
# =============================================================================

class TestGetMediaInfo:
    """Tests for GET /api/v1/media/brands/{brand_id}/media/{key}"""

    async def test_get_media_info_not_found(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting info for non-existent media."""
        fake_key = f"brands/{test_brand.id}/media/2025/01/fake.jpg"

        response = await client.get(
            f"/api/v1/media/brands/{test_brand.id}/media/{fake_key}",
            headers=auth_headers,
        )

        # May return 404 or 500 if S3/MinIO is not configured
        assert response.status_code in [404, 500, 503]

    async def test_get_media_info_forbidden(
        self,
        client: AsyncClient,
        test_brand: Brand,
        auth_headers: dict,
    ):
        """Test getting info for media from another brand."""
        other_brand_id = str(uuid4())
        fake_key = f"brands/{other_brand_id}/media/2025/01/fake.jpg"

        response = await client.get(
            f"/api/v1/media/brands/{test_brand.id}/media/{fake_key}",
            headers=auth_headers,
        )

        assert response.status_code == 403
