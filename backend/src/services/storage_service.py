from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

from jose import JWTError, jwt

from helpers.config import get_settings


class StorageService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._s3 = None
        if self._settings.STORAGE_BACKEND == "s3":
            import boto3
            self._s3 = boto3.client(
                "s3",
                endpoint_url=self._settings.S3_ENDPOINT_URL,
                region_name=self._settings.S3_REGION,
                aws_access_key_id=self._settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=self._settings.S3_SECRET_ACCESS_KEY,
            )

    async def upload(self, local_path: str, key: str, content_type: str) -> str:
        if self._s3 is None:
            return local_path
        await asyncio.to_thread(
            self._s3.upload_file,
            local_path,
            self._settings.S3_BUCKET,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    async def delete(self, *, backend: str, key: str | None, local_path: str | None) -> None:
        if backend == "s3" and self._s3 is not None and key:
            await asyncio.to_thread(self._s3.delete_object, Bucket=self._settings.S3_BUCKET, Key=key)
        elif local_path:
            try:
                Path(local_path).unlink(missing_ok=True)
            except OSError:
                pass

    def inline_url(self, *, backend: str, key: str | None, source_kind: str, source_id: str, filename: str) -> str:
        if backend == "s3" and self._s3 is not None and key:
            return self._s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self._settings.S3_BUCKET,
                    "Key": key,
                    "ResponseContentDisposition": f'inline; filename="{filename}"',
                },
                ExpiresIn=60,
            )
        expire = datetime.now(timezone.utc) + timedelta(seconds=60)
        token = jwt.encode(
            {"kind": source_kind, "id": source_id, "purpose": "citation", "exp": int(expire.timestamp())},
            self._settings.JWT_SECRET,
            algorithm=self._settings.JWT_ALG,
        )
        return f"/api/chat/citations/content?token={quote(token)}"

    def download_url(self, *, key: str, filename: str, content_type: str) -> str:
        """Create a short-lived attachment URL for an object-store file."""
        if self._s3 is None:
            raise ValueError("Object storage is not configured")
        return self._s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self._settings.S3_BUCKET,
                "Key": key,
                "ResponseContentType": content_type,
                "ResponseContentDisposition": f'attachment; filename="{filename}"',
            },
            ExpiresIn=60,
        )

    def verify_local_token(self, token: str) -> tuple[str, str]:
        try:
            payload = jwt.decode(token, self._settings.JWT_SECRET, algorithms=[self._settings.JWT_ALG])
        except JWTError as exc:
            raise ValueError("Invalid or expired citation URL") from exc
        if payload.get("purpose") != "citation":
            raise ValueError("Invalid citation URL")
        return str(payload["kind"]), str(payload["id"])


_storage: StorageService | None = None


def get_storage() -> StorageService:
    global _storage
    if _storage is None:
        _storage = StorageService()
    return _storage
