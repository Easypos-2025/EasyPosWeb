import asyncio
import os
from pathlib import Path

import aiofiles

SPACES_KEY      = os.getenv("SPACES_KEY", "")
SPACES_SECRET   = os.getenv("SPACES_SECRET", "")
SPACES_BUCKET   = os.getenv("SPACES_BUCKET", "easyposweb")
SPACES_REGION   = os.getenv("SPACES_REGION", "nyc3")
SPACES_ENDPOINT = os.getenv("SPACES_ENDPOINT", "https://nyc3.digitaloceanspaces.com")

_USE_SPACES = bool(SPACES_KEY and SPACES_SECRET)
_LOCAL_UPLOADS = Path(__file__).resolve().parent.parent / "uploads"


def _boto_upload(content: bytes, path: str) -> None:
    import boto3
    from botocore.config import Config
    client = boto3.client(
        "s3",
        region_name=SPACES_REGION,
        endpoint_url=SPACES_ENDPOINT,
        aws_access_key_id=SPACES_KEY,
        aws_secret_access_key=SPACES_SECRET,
        config=Config(signature_version="s3v4"),
    )
    client.put_object(Bucket=SPACES_BUCKET, Key=path, Body=content, ACL="public-read")


async def upload_file(content: bytes, path: str) -> str:
    """
    path: ruta relativa, ej. 'images/task1_abc.jpg'
    Retorna URL pública (DO Spaces) o ruta local '/uploads/...'
    """
    if _USE_SPACES:
        await asyncio.to_thread(_boto_upload, content, path)
        return f"{SPACES_ENDPOINT}/{SPACES_BUCKET}/{path}"

    dest = _LOCAL_UPLOADS / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(dest, "wb") as f:
        await f.write(content)
    return f"/uploads/{path}"
