from datetime import UTC, datetime

from app.providers.ceph import CephObjectStorageProvider
from app.providers.types import ObjectPreviewType


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.closed = False

    def read(self, max_bytes: int) -> bytes:
        return self.data[:max_bytes]

    def close(self) -> None:
        self.closed = True


class FakeS3Client:
    def __init__(self, content: bytes, content_type: str, size: int | None = None) -> None:
        self.content = content
        self.content_type = content_type
        self.size = len(content) if size is None else size

    def head_object(self, Bucket: str, Key: str) -> dict:
        return {
            "ContentLength": self.size,
            "ContentType": self.content_type,
            "ETag": '"abc123"',
            "LastModified": datetime(2026, 1, 1, tzinfo=UTC),
            "Metadata": {},
        }

    def get_object(self, Bucket: str, Key: str, Range: str) -> dict:
        return {"Body": FakeBody(self.content)}

    def generate_presigned_url(self, operation: str, Params: dict, ExpiresIn: int) -> str:
        return f"https://preview.example/{Params['Bucket']}/{Params['Key']}"


def provider_with_client(client: FakeS3Client) -> CephObjectStorageProvider:
    provider = object.__new__(CephObjectStorageProvider)
    provider.endpoint_url = "https://rgw.example"
    provider.default_bucket = None
    provider._client = client
    return provider


def test_json_preview_pretty_prints_limited_content() -> None:
    provider = provider_with_client(FakeS3Client(b'{"b":2,"a":1}', "application/json"))

    preview = provider.get_object_preview("bucket", "data.json")

    assert preview.preview_type == ObjectPreviewType.JSON
    assert preview.text == '{\n  "a": 1,\n  "b": 2\n}'
    assert preview.download_url == "https://preview.example/bucket/data.json"


def test_image_preview_returns_presigned_url_without_reading_bytes() -> None:
    provider = provider_with_client(FakeS3Client(b"image-bytes", "image/png", size=5_000_000))

    preview = provider.get_object_preview("bucket", "image.png")

    assert preview.preview_type == ObjectPreviewType.IMAGE
    assert preview.image_url == "https://preview.example/bucket/image.png"
    assert preview.download_url == "https://preview.example/bucket/image.png"


def test_unsupported_preview_is_friendly() -> None:
    provider = provider_with_client(FakeS3Client(b"hello", "application/octet-stream"))

    preview = provider.get_object_preview("bucket", "archive.bin")

    assert preview.preview_type == ObjectPreviewType.UNSUPPORTED
    assert preview.reason == "Object type is not supported for inline preview."
    assert preview.download_url == "https://preview.example/bucket/archive.bin"
