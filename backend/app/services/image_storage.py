import hashlib
import time
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StoredImageResult:
    """Represents the outcome of a successful image upload."""
    image_url: str
    public_id: str
    file_size_bytes: int
    content_type: str


class ImageStorageProvider(ABC):
    """Abstract interface for image evidence storage."""

    @abstractmethod
    async def upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> StoredImageResult:
        """Upload image bytes and return storage metadata."""
        pass

    @abstractmethod
    async def delete_image(self, public_id: str) -> bool:
        """Remove an image by its storage public identifier."""
        pass


class CloudinaryImageStorageProvider(ImageStorageProvider):
    """
    Production storage provider integrating directly with Cloudinary REST API via httpx.
    Requires CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET.
    """

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        folder: str = "civicpulse/complaints",
    ):
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.folder = folder
        self.upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
        self.destroy_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/destroy"

    def _generate_signature(self, params: dict) -> str:
        """Calculates Cloudinary API signature by sorting parameter keys and appending api_secret."""
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        to_sign = f"{sorted_params}{self.api_secret}"
        return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

    async def upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> StoredImageResult:
        timestamp = int(time.time())
        params_to_sign = {
            "folder": self.folder,
            "timestamp": timestamp,
        }
        signature = self._generate_signature(params_to_sign)

        data = {
            "api_key": self.api_key,
            "timestamp": str(timestamp),
            "folder": self.folder,
            "signature": signature,
        }
        files = {
            "file": (filename, file_bytes, content_type)
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.upload_url, data=data, files=files)
            if response.status_code != 200:
                logger.error("Cloudinary upload failed: %s", response.text)
                raise RuntimeError(f"Cloudinary image upload failed with HTTP {response.status_code}")

            result = response.json()
            return StoredImageResult(
                image_url=result["secure_url"],
                public_id=result["public_id"],
                file_size_bytes=len(file_bytes),
                content_type=content_type,
            )

    async def delete_image(self, public_id: str) -> bool:
        timestamp = int(time.time())
        params_to_sign = {
            "public_id": public_id,
            "timestamp": timestamp,
        }
        signature = self._generate_signature(params_to_sign)

        data = {
            "public_id": public_id,
            "api_key": self.api_key,
            "timestamp": str(timestamp),
            "signature": signature,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(self.destroy_url, data=data)
            return response.status_code == 200


class MockImageStorageProvider(ImageStorageProvider):
    """
    In-memory mock storage provider for unit testing and local development
    where real Cloudinary credentials are not provisioned.
    """

    def __init__(self):
        self.stored_files: dict[str, bytes] = {}

    async def upload_image(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> StoredImageResult:
        image_id = str(uuid.uuid4())
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        public_id = f"civicpulse/complaints/{image_id}"
        image_url = f"https://res.cloudinary.com/civicpulse-mock/image/upload/v1/{public_id}.{ext}"

        self.stored_files[public_id] = file_bytes
        return StoredImageResult(
            image_url=image_url,
            public_id=public_id,
            file_size_bytes=len(file_bytes),
            content_type=content_type,
        )

    async def delete_image(self, public_id: str) -> bool:
        if public_id in self.stored_files:
            del self.stored_files[public_id]
            return True
        return False

    def clear(self) -> None:
        self.stored_files.clear()


# Active singleton instance for dependency injection
_storage_provider_instance: Optional[ImageStorageProvider] = None


def get_image_storage_provider() -> ImageStorageProvider:
    """Returns the active image storage provider based on configuration."""
    global _storage_provider_instance
    if _storage_provider_instance is not None:
        return _storage_provider_instance

    if (
        settings.CLOUDINARY_CLOUD_NAME
        and settings.CLOUDINARY_API_KEY
        and settings.CLOUDINARY_API_SECRET
    ):
        logger.info("Using CloudinaryImageStorageProvider for evidence photos.")
        return CloudinaryImageStorageProvider(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            folder=settings.CLOUDINARY_FOLDER,
        )

    logger.debug("Cloudinary credentials not provisioned; using MockImageStorageProvider.")
    return MockImageStorageProvider()


def set_image_storage_provider(provider: Optional[ImageStorageProvider]) -> None:
    """Allows test fixtures to override the active storage provider."""
    global _storage_provider_instance
    _storage_provider_instance = provider
