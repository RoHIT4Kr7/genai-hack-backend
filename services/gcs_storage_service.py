"""
Google Cloud Storage service for production use with calmira-backend bucket.
"""

import os
import uuid
from typing import Optional, List
from loguru import logger
from google.cloud import storage
from config.settings import settings


class GCSStorageService:
    """Google Cloud Storage service for manga assets."""

    def __init__(self):
        self.bucket_name = settings.gcs_bucket_name  # calmira-backend
        self.client = None
        self.bucket = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize Google Cloud Storage client."""
        try:
            # Initialize GCS client using GOOGLE_APPLICATION_CREDENTIALS
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)

            logger.info(
                f"✅ Google Cloud Storage initialized with bucket: {self.bucket_name}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud Storage: {e}")
            raise

    async def upload_bytes(self, data: bytes, path: str) -> str:
        """Upload bytes to GCS and return signed URL."""
        try:
            # Create blob with the specified path
            blob = self.bucket.blob(path)

            # Upload the data
            blob.upload_from_string(data)

            # Generate signed URL (valid for 24 hours)
            from datetime import timedelta
            signed_url = blob.generate_signed_url(
                expiration=timedelta(hours=24),
                method="GET"
            )
            
            logger.info(f"Uploaded to GCS: {path} -> signed URL generated")
            return signed_url

        except Exception as e:
            logger.error(f"Failed to upload to GCS {path}: {e}")
            return ""

    async def upload_reference_image(
        self, data: bytes, story_id: str, ref_number: int
    ) -> str:
        """Upload reference image to GCS."""
        path = f"stories/{story_id}/reference_{ref_number:02d}.png"
        return await self.upload_bytes(data, path)

    async def upload_image(self, data: bytes, story_id: str, panel_number: int) -> str:
        """Upload panel image to GCS."""
        path = f"stories/{story_id}/panel_{panel_number:02d}.png"
        return await self.upload_bytes(data, path)

    async def check_bucket_access(self) -> bool:
        """Check if bucket is accessible."""
        try:
            # Try to list objects (with limit to avoid large responses)
            blobs = list(self.client.list_blobs(self.bucket_name, max_results=1))
            logger.info(f"✅ GCS bucket access verified: {self.bucket_name}")
            return True

        except Exception as e:
            logger.error(f"GCS bucket access failed: {e}")
            return False

    async def get_story_assets(self, story_id: str) -> List[str]:
        """Get list of assets for a story with signed URLs."""
        try:
            prefix = f"stories/{story_id}/"
            blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)

            assets = []
            from datetime import timedelta
            
            for blob in blobs:
                # Generate signed URL (valid for 24 hours)
                signed_url = blob.generate_signed_url(
                    expiration=timedelta(hours=24),
                    method="GET"
                )
                assets.append(signed_url)

            return assets

        except Exception as e:
            logger.error(f"Failed to get story assets for {story_id}: {e}")
            return []


# Global GCS storage service instance
gcs_storage_service = GCSStorageService()
