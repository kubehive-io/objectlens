from unittest.mock import patch

import httpx
import pytest

from server import (
    _format_error,
    get_default_provider,
    get_object_metadata,
    get_object_preview,
    list_activities,
    list_bucket_objects,
    list_buckets,
    list_providers,
    scan_bucket,
    search_objects,
)


@pytest.fixture
def mock_request():
    return httpx.Request("GET", "http://localhost:8000")


@pytest.mark.asyncio
async def test_format_error():
    req = httpx.Request("GET", "http://localhost:8000/providers")
    resp = httpx.Response(400, text="Bad Request", request=req)
    status_err = httpx.HTTPStatusError("HTTP Error", request=req, response=resp)
    assert "returned status 400" in _format_error(status_err)

    conn_err = httpx.ConnectError("Connection refused", request=req)
    assert "Failed to connect to ObjectLens" in _format_error(conn_err)


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_list_providers_success(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/providers")
    mock_get.return_value = httpx.Response(
        200,
        json=[
            {
                "id": "aws-prod",
                "name": "AWS Production",
                "provider": "aws",
                "endpoint_url": None,
                "default_bucket": "prod-bucket",
            }
        ],
        request=req,
    )
    res = await list_providers()
    assert "### Configured S3 Storage Providers" in res
    assert "AWS Production" in res
    assert "prod-bucket" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_list_providers_empty(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/providers")
    mock_get.return_value = httpx.Response(200, json=[], request=req)
    res = await list_providers()
    assert "No storage providers configured" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_default_provider(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/provider")
    mock_get.return_value = httpx.Response(
        200,
        json={
            "id": "ceph-home",
            "name": "Ceph Home",
            "provider": "ceph",
            "endpoint_url": "http://192.168.1.100:8080",
            "default_bucket": "backup",
        },
        request=req,
    )
    res = await get_default_provider()
    assert "### Default Storage Provider Details" in res
    assert "Ceph Home" in res
    assert "http://192.168.1.100:8080" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_list_buckets(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/buckets")
    mock_get.return_value = httpx.Response(
        200,
        json={
            "buckets": [
                {"name": "logs-bucket", "creation_date": "2026-07-12T12:00:00Z"},
                {"name": "data-bucket", "creation_date": None},
            ]
        },
        request=req,
    )
    res = await list_buckets()
    assert "### Buckets for Provider" in res
    assert "logs-bucket" in res
    assert "data-bucket" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_list_bucket_objects(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/buckets/test-bucket/objects")
    mock_get.return_value = httpx.Response(
        200,
        json={
            "items": [
                {
                    "type": "prefix",
                    "prefix": "data/processed/",
                    "name": "processed",
                    "icon": "folder",
                },
                {
                    "type": "object",
                    "key": "data/test.json",
                    "size": 2048,
                    "content_type": "application/json",
                    "last_modified": "2026-07-12T12:30:00Z",
                },
            ],
            "total": 2,
            "mode": "browse",
        },
        request=req,
    )
    res = await list_bucket_objects("test-bucket", prefix="data/")
    assert "### Objects in Bucket 'test-bucket'" in res
    assert "Folders:" in res
    assert "data/processed/" in res
    assert "Objects:" in res
    assert "data/test.json" in res
    assert "2.00 KB" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_object_metadata(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/objects/metadata")
    mock_get.return_value = httpx.Response(
        200,
        json={
            "bucket": "data-bucket",
            "provider": "garage-local",
            "key": "test.txt",
            "size": 512,
            "content_type": "text/plain",
            "last_modified": "2026-07-12T12:00:00Z",
            "etag": '"abc123xyz"',
            "storage_class": "STANDARD",
            "indexed_at": "2026-07-12T12:01:00Z",
        },
        request=req,
    )
    res = await get_object_metadata("data-bucket", "test.txt")
    assert "### Object Metadata: `test.txt`" in res
    assert "Size**: 512 bytes" in res
    assert "text/plain" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_get_object_preview(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/objects/preview")
    mock_get.return_value = httpx.Response(
        200,
        json={
            "content_type": "text/markdown",
            "size": 25,
            "truncated": False,
            "encoding": "utf-8",
            "content": "# Hello World\nThis is a test.",
        },
        request=req,
    )
    res = await get_object_preview("data-bucket", "test.md")
    assert "### Preview of `test.md` in Bucket `data-bucket`" in res
    assert "# Hello World" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_search_objects(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/objects")
    mock_get.return_value = httpx.Response(
        200,
        json={
            "objects": [
                {
                    "bucket": "assets",
                    "provider": "aws-prod",
                    "key": "images/logo.png",
                    "size": 15000,
                    "content_type": "image/png",
                    "last_modified": "2026-07-12T12:00:00Z",
                }
            ],
            "count": 1,
        },
        request=req,
    )
    res = await search_objects("logo")
    assert "### Metadata Search Results" in res
    assert "images/logo.png" in res
    assert "14.65 KB" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.post")
async def test_scan_bucket(mock_post):
    req = httpx.Request("POST", "http://localhost:8000/index/scan")
    mock_post.return_value = httpx.Response(
        200,
        json={"bucket": "demo-bucket", "scanned": 150, "indexed": 12},
        request=req,
    )
    res = await scan_bucket("demo-bucket")
    assert "### Index Scan Completed for Bucket `demo-bucket`" in res
    assert "Scanned S3 objects: 150" in res
    assert "Indexed/updated database records: 12" in res


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_list_activities(mock_get):
    req = httpx.Request("GET", "http://localhost:8000/activity")
    mock_get.return_value = httpx.Response(
        200,
        json=[
            {
                "type": "success",
                "title": "Bucket Metadata Indexed",
                "description": "Scanned bucket demo and indexed 12 records.",
                "timestamp": "2026-07-12T12:00:00Z",
            }
        ],
        request=req,
    )
    res = await list_activities()
    assert "### Recent Activities" in res
    assert "Bucket Metadata Indexed" in res
    assert "Scanned bucket demo" in res
