"""MinIO client for document upload/download with presigned URLs."""

from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import timedelta
import uuid

from config import settings

minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE,
)


def ensure_bucket():
    """Create bucket if it doesn't exist."""
    bucket = settings.MINIO_BUCKET_DOCUMENTS
    if not minio_client.bucket_exists(bucket):
        minio_client.make_bucket(bucket)


def upload_file(file_data: bytes, content_type: str, folder: str = "documents") -> str:
    """Upload a file to MinIO and return its key."""
    ensure_bucket()
    file_key = f"{folder}/{uuid.uuid4().hex}"
    minio_client.put_object(
        settings.MINIO_BUCKET_DOCUMENTS,
        file_key,
        BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    return file_key


def download_file(file_key: str) -> bytes:
    """Download a file from MinIO."""
    response = minio_client.get_object(settings.MINIO_BUCKET_DOCUMENTS, file_key)
    data = response.read()
    response.close()
    response.release_conn()
    return data


def get_presigned_url(file_key: str, expires: int = 3600) -> str:
    """Generate a presigned URL for temporary access (default 1 hour)."""
    return minio_client.presigned_get_object(
        settings.MINIO_BUCKET_DOCUMENTS,
        file_key,
        expires=timedelta(seconds=expires),
    )


def delete_file(file_key: str) -> None:
    """Delete a file from MinIO."""
    minio_client.remove_object(settings.MINIO_BUCKET_DOCUMENTS, file_key)
