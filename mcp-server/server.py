import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic_settings import BaseSettings


# Define configuration settings with pydantic-settings
class Settings(BaseSettings):
    api_url: str = "http://localhost:8000"
    username: str | None = None
    password: str | None = None

    class Config:
        env_prefix = "OBJECTLENS_"


settings = Settings()

# Set up logging to stderr. Stdout is reserved for JSON-RPC messages.
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("objectlens-mcp")

# Initialize FastMCP Server
mcp = FastMCP(
    "ObjectLens",
    instructions=(
        "Interface with S3-compatible cloud storage, manage bucket indexes, and search metadata."
    ),
)


@asynccontextmanager
async def get_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an authenticated HTTP client to interact with ObjectLens REST API."""
    auth = None
    if settings.username and settings.password:
        auth = httpx.BasicAuth(settings.username, settings.password)

    async with httpx.AsyncClient(base_url=settings.api_url, auth=auth, timeout=30.0) as client:
        yield client


def _format_error(err: Exception) -> str:
    """Format HTTP or connection errors cleanly for the model."""
    if isinstance(err, httpx.HTTPStatusError):
        return (
            f"Error: ObjectLens API returned status {err.response.status_code}. "
            f"Detail: {err.response.text}"
        )
    if isinstance(err, httpx.RequestError):
        return (
            f"Error: Failed to connect to ObjectLens API at {settings.api_url}. "
            "Is the service running?"
        )
    return f"Error: {err}"


@mcp.tool()
async def list_providers() -> str:
    """
    List S3-compatible storage providers configured in ObjectLens.
    """
    try:
        async with get_client() as client:
            resp = await client.get("/providers")
            resp.raise_for_status()
            providers = resp.json()

            if not providers:
                return "No storage providers configured in ObjectLens."

            lines = ["### Configured S3 Storage Providers"]
            for p in providers:
                lines.append(
                    f"- **{p['name']}** (ID: `{p['id']}`)\n"
                    f"  - Provider Type: {p['provider']}\n"
                    f"  - Endpoint URL: {p['endpoint_url'] or 'Default'}\n"
                    f"  - Default Bucket: {p['default_bucket'] or 'None'}"
                )
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def get_default_provider() -> str:
    """
    Get connection details of the default/active storage provider.
    """
    try:
        async with get_client() as client:
            resp = await client.get("/provider")
            resp.raise_for_status()
            p = resp.json()

            lines = [
                "### Default Storage Provider Details",
                f"- **Name**: {p['name']}",
                f"- **Connection ID**: `{p['id']}`",
                f"- **Provider Type**: {p['provider']}",
                f"- **Endpoint URL**: {p['endpoint_url'] or 'Default S3'}",
                f"- **Default Bucket**: {p['default_bucket'] or 'None'}",
            ]
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def list_buckets(provider_id: str | None = None) -> str:
    """
    List all S3 buckets for a specific provider, or the default provider if not specified.

    :param provider_id: Optional connection ID of the provider.
    """
    try:
        async with get_client() as client:
            url = f"/providers/{provider_id}/buckets" if provider_id else "/buckets"
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            buckets = data.get("buckets", [])

            if not buckets:
                return f"No buckets found for provider '{provider_id or 'default'}'."

            lines = [f"### Buckets for Provider '{provider_id or 'default'}'"]
            for b in buckets:
                lines.append(f"- **{b['name']}** (Created: {b['creation_date'] or 'Unknown'})")
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def list_bucket_objects(
    bucket: str,
    prefix: str = "",
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    delimiter: str = "/",
    provider_id: str | None = None,
) -> str:
    """
    List or search objects inside a specific bucket, with prefix filtering and pagination.

    :param bucket: The bucket name to query.
    :param prefix: Optional prefix/folder path (e.g. 'data/').
    :param search: Optional search pattern or glob string (e.g. '*.json').
    :param limit: Maximum items to return (default is 50).
    :param offset: Offset for pagination (default is 0).
    :param delimiter: Path separator (default is '/').
    :param provider_id: Optional provider connection ID.
    """
    try:
        async with get_client() as client:
            url = (
                f"/providers/{provider_id}/buckets/{bucket}/objects"
                if provider_id
                else f"/buckets/{bucket}/objects"
            )
            params = {
                "prefix": prefix,
                "limit": limit,
                "offset": offset,
                "delimiter": delimiter,
            }
            if search:
                params["search"] = search

            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            total = data.get("total", len(items))
            mode = data.get("mode", "browse")

            if not items:
                return (
                    f"No objects or folders found in bucket '{bucket}' "
                    f"under prefix '{prefix}' (search: '{search or 'none'}')."
                )

            lines = [
                f"### Objects in Bucket '{bucket}' (Mode: {mode}, Total: {total})",
                f"Path: `{prefix or '/'}`",
                "",
            ]

            # Group into folders and files
            folders = [i for i in items if i.get("type") == "prefix"]
            objects = [i for i in items if i.get("type") == "object"]

            if folders:
                lines.append("#### Folders:")
                for f in folders:
                    lines.append(f"- 📁 `{f['prefix']}`")
                lines.append("")

            if objects:
                lines.append("#### Objects:")
                for o in objects:
                    size_kb = o.get("size", 0) / 1024
                    lines.append(
                        f"- 📄 `{o['key']}` "
                        f"({size_kb:.2f} KB, "
                        f"Type: {o.get('content_type') or 'binary'}, "
                        f"Modified: {o.get('last_modified') or 'Unknown'})"
                    )
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def get_object_metadata(bucket: str, key: str, provider_id: str | None = None) -> str:
    """
    Get detailed metadata for a specific object in a bucket.

    :param bucket: Name of the bucket.
    :param key: Unique key/path of the object.
    :param provider_id: Optional provider connection ID.
    """
    try:
        async with get_client() as client:
            url = (
                f"/providers/{provider_id}/objects/metadata" if provider_id else "/objects/metadata"
            )
            params = {"bucket": bucket, "key": key}
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            meta = resp.json()

            size_kb = meta.get("size", 0) / 1024
            lines = [
                f"### Object Metadata: `{key}`",
                f"- **Bucket**: {bucket}",
                f"- **Provider**: {meta.get('provider') or provider_id or 'default'}",
                f"- **Size**: {meta.get('size', 0)} bytes ({size_kb:.2f} KB)",
                f"- **Content Type**: {meta.get('content_type') or 'Unknown'}",
                f"- **Last Modified**: {meta.get('last_modified') or 'Unknown'}",
                f"- **ETag**: `{meta.get('etag') or 'None'}`",
                f"- **Storage Class**: {meta.get('storage_class') or 'Standard'}",
                f"- **Indexed At**: {meta.get('indexed_at') or 'Not indexed'}",
            ]
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def get_object_preview(
    bucket: str, key: str, max_bytes: int = 1048576, provider_id: str | None = None
) -> str:
    """
    Read the contents or preview of an S3 object. Useful for text, JSON, CSV, or code files.

    :param bucket: Name of the bucket.
    :param key: Unique key/path of the object.
    :param max_bytes: Maximum number of bytes to retrieve (default is 1MB).
    :param provider_id: Optional provider connection ID.
    """
    try:
        async with get_client() as client:
            url = f"/providers/{provider_id}/objects/preview" if provider_id else "/objects/preview"
            params = {"bucket": bucket, "key": key, "max_bytes": max_bytes}
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            preview = resp.json()

            lines = [
                f"### Preview of `{key}` in Bucket `{bucket}`",
                f"- **Content Type**: {preview.get('content_type') or 'Unknown'}",
                f"- **Size**: {preview.get('size', 0)} bytes",
                f"- **Truncated**: {preview.get('truncated', False)}",
                f"- **Encoding**: {preview.get('encoding') or 'utf-8'}",
                "---",
                preview.get("content") or "[Empty or Binary Object]",
            ]
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def search_objects(
    search: str,
    bucket: str | None = None,
    prefix: str | None = None,
    limit: int = 100,
    offset: int = 0,
    provider_id: str | None = None,
) -> str:
    """
    Search indexed object metadata in ObjectLens using a query pattern.

    :param search: Broad search query (e.g. partial file name or type).
    :param bucket: Optional bucket name to scope the search.
    :param prefix: Optional prefix to scope the search.
    :param limit: Maximum search results (default 100).
    :param offset: Offset for pagination.
    :param provider_id: Optional provider connection ID.
    """
    try:
        async with get_client() as client:
            params = {
                "search": search,
                "limit": limit,
                "offset": offset,
            }
            if bucket:
                params["bucket"] = bucket
            if prefix:
                params["prefix"] = prefix
            if provider_id:
                params["provider_id"] = provider_id

            resp = await client.get("/objects", params=params)
            resp.raise_for_status()
            data = resp.json()
            objects = data.get("objects", [])
            count = data.get("count", len(objects))

            if not objects:
                return f"No indexed objects matched search query '{search}'."

            lines = [f"### Metadata Search Results (Found {count} matches)"]
            for o in objects:
                size_kb = o.get("size", 0) / 1024
                lines.append(
                    f"- **{o['key']}** (Bucket: `{o['bucket']}`, Provider: `{o['provider']}`)\n"
                    f"  - Size: {size_kb:.2f} KB | "
                    f"Type: {o.get('content_type') or 'binary'} | "
                    f"Modified: {o.get('last_modified') or 'Unknown'}"
                )
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def scan_bucket(bucket: str, provider_id: str | None = None) -> str:
    """
    Trigger a S3 bucket metadata scan to index object records into ObjectLens database.

    :param bucket: The S3 bucket to index.
    :param provider_id: Optional provider connection ID.
    """
    try:
        async with get_client() as client:
            url = f"/providers/{provider_id}/index/scan" if provider_id else "/index/scan"
            resp = await client.post(url, params={"bucket": bucket})
            resp.raise_for_status()
            result = resp.json()

            return (
                f"### Index Scan Completed for Bucket `{bucket}`\n"
                f"- Scanned S3 objects: {result.get('scanned', 0)}\n"
                f"- Indexed/updated database records: {result.get('indexed', 0)}"
            )
    except Exception as exc:
        return _format_error(exc)


@mcp.tool()
async def list_activities(limit: int = 10, offset: int = 0) -> str:
    """
    List recent S3 activities/logs indexed in ObjectLens.

    :param limit: Maximum activities to list (default is 10).
    :param offset: Offset for pagination.
    """
    try:
        async with get_client() as client:
            resp = await client.get("/activity", params={"limit": limit, "offset": offset})
            resp.raise_for_status()
            activities = resp.json()

            if not activities:
                return "No activity logs found in ObjectLens."

            lines = ["### Recent Activities"]
            for a in activities:
                # Type indicator
                icon = "ℹ️"
                if a.get("type") == "error":
                    icon = "❌"
                elif a.get("type") == "warning":
                    icon = "⚠️"
                elif a.get("type") == "success":
                    icon = "✅"

                lines.append(
                    f"- {icon} **{a['title']}** ({a.get('timestamp') or 'Unknown'})\n"
                    f"  - {a.get('description', '')}"
                )
            return "\n".join(lines)
    except Exception as exc:
        return _format_error(exc)


if __name__ == "__main__":
    mcp.run()
