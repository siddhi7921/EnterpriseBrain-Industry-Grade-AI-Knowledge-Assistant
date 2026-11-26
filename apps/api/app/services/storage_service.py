from __future__ import annotations

import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Object storage abstraction supporting S3/MinIO with automatic local filesystem fallback."""

    def __init__(self) -> None:
        self.backend = settings.STORAGE_BACKEND
        self.local_dir = Path(settings.LOCAL_STORAGE_DIR)
        self.local_dir.mkdir(parents=True, exist_ok=True)
        self._s3_client = None

    def _get_s3(self):
        if self._s3_client is None:
            import boto3
            from botocore.client import Config

            self._s3_client = boto3.client(
                "s3",
                endpoint_url=settings.STORAGE_ENDPOINT,
                aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                config=Config(signature_version="s3v4"),
                region_name="us-east-1",
            )
            try:
                self._s3_client.head_bucket(Bucket=settings.STORAGE_BUCKET)
            except Exception:
                self._s3_client.create_bucket(Bucket=settings.STORAGE_BUCKET)
        return self._s3_client

    def put_bytes(self, storage_key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        if self.backend == "s3":
            try:
                client = self._get_s3()
                client.put_object(
                    Bucket=settings.STORAGE_BUCKET,
                    Key=storage_key,
                    Body=data,
                    ContentType=content_type,
                )
                return
            except Exception as exc:
                logger.warning("S3 upload unavailable (%s); falling back to local storage.", exc)

        target = self.local_dir / storage_key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def get_bytes(self, storage_key: str) -> bytes:
        if self.backend == "s3":
            try:
                client = self._get_s3()
                obj = client.get_object(Bucket=settings.STORAGE_BUCKET, Key=storage_key)
                return obj["Body"].read()
            except Exception as exc:
                logger.warning("S3 read unavailable (%s); reading from local storage.", exc)

        target = self.local_dir / storage_key
        if not target.exists():
            raise FileNotFoundError(f"Object not found in storage: {storage_key}")
        return target.read_bytes()

    def delete_object(self, storage_key: str) -> None:
        if self.backend == "s3":
            try:
                client = self._get_s3()
                client.delete_object(Bucket=settings.STORAGE_BUCKET, Key=storage_key)
            except Exception:
                pass
        target = self.local_dir / storage_key
        if target.exists():
            target.unlink()


storage_service = StorageService()
