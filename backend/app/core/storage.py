import os
from typing import Optional

import boto3
from botocore.client import Config

# MinIO uses S3-compatible API — same code works for AWS S3
_client = None


def get_storage_client():
    """Get or create the MinIO/S3 client (singleton)."""
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=f"http://{os.environ.get('MINIO_ENDPOINT', 'minio:9000')}",
            aws_access_key_id=os.environ.get("MINIO_ROOT_USER", "minioadmin"),
            aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin123"),
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
    return _client


def ensure_bucket_exists(bucket_name: str) -> None:
    """Create bucket if it doesn't exist."""
    client = get_storage_client()
    try:
        client.head_bucket(Bucket=bucket_name)
    except Exception:
        client.create_bucket(Bucket=bucket_name)


def upload_file(
    file_bytes: bytes,
    bucket: str,
    object_key: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload a file to MinIO/S3.
    Returns the object key (path) — NOT a public URL.
    """
    ensure_bucket_exists(bucket)
    client = get_storage_client()
    client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return object_key


def generate_presigned_url(bucket: str, object_key: str, expiry_seconds: int = 300) -> str:
    """
    Generate a short-lived URL for secure file access.
    Default: 5 minutes (300 seconds).
    Only users with a valid signed URL can access the file.
    """
    client = get_storage_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=expiry_seconds,
    )
    return url


def delete_file(bucket: str, object_key: str) -> None:
    """Delete a file from storage."""
    client = get_storage_client()
    client.delete_object(Bucket=bucket, Key=object_key)
