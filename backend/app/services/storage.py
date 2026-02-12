"""
PresenceOS - Storage Service (S3/MinIO)
"""
import uuid
import structlog
from datetime import datetime, timedelta
from typing import BinaryIO

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = structlog.get_logger()


class StorageService:
    """Service for managing file storage on S3/MinIO."""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = settings.s3_bucket_name
        self.public_url = settings.s3_public_url or settings.s3_endpoint_url

    async def ensure_bucket_exists(self) -> bool:
        """Ensure the storage bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info("Created S3 bucket", bucket=self.bucket_name)
                    return True
                except Exception as create_error:
                    logger.error("Failed to create bucket", error=str(create_error))
                    return False
            logger.error("Error checking bucket", error=str(e))
            return False

    def generate_key(
        self,
        brand_id: str,
        media_type: str,
        original_filename: str,
    ) -> str:
        """
        Generate a unique key for storing a file.
        Format: brands/{brand_id}/media/{YYYY}/{MM}/{uuid}_{filename}
        """
        now = datetime.utcnow()
        file_uuid = uuid.uuid4().hex[:12]
        safe_filename = original_filename.replace(" ", "_")

        return f"brands/{brand_id}/media/{now.year}/{now.month:02d}/{file_uuid}_{safe_filename}"

    async def upload_file(
        self,
        file: BinaryIO,
        key: str,
        content_type: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """
        Upload a file to storage.

        Returns:
            {
                "key": str,
                "url": str,
                "size": int,
            }
        """
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if metadata:
            extra_args["Metadata"] = metadata

        # Get file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        try:
            self.client.upload_fileobj(
                file,
                self.bucket_name,
                key,
                ExtraArgs=extra_args,
            )

            url = self.get_public_url(key)

            logger.info("File uploaded", key=key, size=size)

            return {
                "key": key,
                "url": url,
                "size": size,
            }
        except Exception as e:
            logger.error("Upload failed", key=key, error=str(e))
            raise

    async def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Upload bytes to storage."""
        from io import BytesIO
        return await self.upload_file(
            BytesIO(data),
            key,
            content_type,
            metadata,
        )

    def get_public_url(self, key: str) -> str:
        """Get the public URL for a stored file."""
        if self.public_url:
            base = self.public_url.rstrip("/")
            # Avoid duplicating bucket name if public_url already includes it
            # e.g. S3_PUBLIC_URL=http://localhost:9000/presenceos-media
            if base.endswith(f"/{self.bucket_name}"):
                return f"{base}/{key}"
            return f"{base}/{self.bucket_name}/{key}"
        return f"https://{self.bucket_name}.s3.{settings.s3_region}.amazonaws.com/{key}"

    def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        for_upload: bool = False,
        content_type: str | None = None,
    ) -> str:
        """
        Generate a presigned URL for direct upload or download.

        Args:
            key: The storage key
            expires_in: URL validity in seconds (default 1 hour)
            for_upload: If True, generate URL for PUT operation
            content_type: Content type for upload (required if for_upload)
        """
        if for_upload:
            params = {
                "Bucket": self.bucket_name,
                "Key": key,
            }
            if content_type:
                params["ContentType"] = content_type

            url = self.client.generate_presigned_url(
                "put_object",
                Params=params,
                ExpiresIn=expires_in,
            )
        else:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                },
                ExpiresIn=expires_in,
            )

        return url

    async def delete_file(self, key: str) -> bool:
        """Delete a file from storage."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key,
            )
            logger.info("File deleted", key=key)
            return True
        except Exception as e:
            logger.error("Delete failed", key=key, error=str(e))
            return False

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in storage."""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    async def get_file_info(self, key: str) -> dict | None:
        """Get metadata about a stored file."""
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                "key": key,
                "size": response["ContentLength"],
                "content_type": response.get("ContentType"),
                "last_modified": response["LastModified"],
                "metadata": response.get("Metadata", {}),
            }
        except ClientError:
            return None


# Singleton instance
_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    """Get or create the storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
