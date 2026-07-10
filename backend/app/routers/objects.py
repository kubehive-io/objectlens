import mimetypes
from typing import Annotated

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from ..config import get_settings
from ..db import delete_object_metadata, delete_prefix_metadata, search_objects, upsert_objects
from ..models import (
    DeleteObjectResponse,
    DeletePrefixResponse,
    MergePrefixesRequest,
    MergePrefixesResponse,
    MoveItem,
    MoveObjectsRequest,
    ObjectListResponse,
    ObjectMetadata,
    ObjectOperationSummary,
    ObjectPreviewResponse,
    OperationStatus,
    PresignDownloadResponse,
    RenameObjectRequest,
    RenamePrefixRequest,
    UploadObjectResponse,
)
from ..operations import create_operation, get_operation, update_operation
from ..providers import get_provider, get_provider_by_id

router = APIRouter(tags=["objects"])


def _provider_or_error(provider_id: str | None = None):
    try:
        return get_provider_by_id(provider_id) if provider_id else get_provider(get_settings())
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _provider_key(provider) -> str:
    return getattr(provider, "connection_id", provider.provider)


def _normalize_prefix(prefix: str) -> str:
    normalized = prefix.strip("/")
    return f"{normalized}/" if normalized else ""


def _object_name(key: str) -> str:
    return key.rstrip("/").rsplit("/", 1)[-1]


def _storage_error(message: str, exc: Exception) -> HTTPException:
    return HTTPException(status_code=502, detail=f"{message}: {exc}")


def _object_exists(provider, bucket: str, key: str) -> bool:
    try:
        provider.get_object_metadata(bucket=bucket, key=key)
        return True
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def _list_prefix_objects(provider, bucket: str, prefix: str) -> list[str]:
    keys: list[str] = []
    continuation_token = None
    while True:
        result = provider.list_objects(
            bucket=bucket,
            prefix=prefix,
            delimiter=None,
            continuation_token=continuation_token,
            limit=1000,
        )
        keys.extend(item.key for item in result.objects)
        continuation_token = result.next_continuation_token
        if not continuation_token:
            return keys


def _copy_then_delete(provider, bucket: str, source_key: str, target_key: str) -> ObjectMetadata:
    provider_key = _provider_key(provider)
    metadata = provider.copy_object(bucket=bucket, source_key=source_key, target_key=target_key)
    provider.delete_object(bucket=bucket, key=source_key)
    delete_object_metadata(provider_key, bucket, source_key)
    upsert_objects(provider_key, bucket, [metadata.model_dump()])
    return ObjectMetadata(
        provider=provider_key,
        bucket=bucket,
        indexed_at=metadata.last_modified,
        **metadata.model_dump(),
    )


def _prefix_move_plan(
    source_prefix: str,
    target_prefix: str,
    keys: list[str],
) -> list[tuple[str, str]]:
    return [(key, f"{target_prefix}{key[len(source_prefix) :]}") for key in keys]


def _move_plan_for_items(
    provider,
    bucket: str,
    items: list[MoveItem],
    target_prefix: str,
) -> list[tuple[str, str, str | None]]:
    plan: list[tuple[str, str, str | None]] = []
    for item in items:
        if item.type == "object" and item.key:
            plan.append((item.key, f"{target_prefix}{_object_name(item.key)}", None))
        elif item.type == "prefix" and item.prefix:
            source_prefix = _normalize_prefix(item.prefix)
            if not source_prefix:
                raise HTTPException(status_code=400, detail="Cannot move the bucket root prefix.")
            prefix_name = _object_name(source_prefix) + "/"
            for key in _list_prefix_objects(provider, bucket, source_prefix):
                plan.append(
                    (
                        key,
                        f"{target_prefix}{prefix_name}{key[len(source_prefix) :]}",
                        source_prefix,
                    )
                )
    return plan


def _conflicts(provider, bucket: str, target_keys: list[str]) -> list[str]:
    conflicts = []
    for key in target_keys:
        if _object_exists(provider, bucket, key):
            conflicts.append(key)
    return conflicts


@router.get("/objects", response_model=ObjectListResponse)
def objects(
    bucket: str = Query(..., min_length=1),
    prefix: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> ObjectListResponse:
    # TODO: Add OpenSearch support for large-scale metadata search.
    provider = _provider_or_error()
    provider_key = _provider_key(provider)
    rows = search_objects(
        provider=provider_key,
        bucket=bucket,
        prefix=prefix,
        search=search,
        limit=limit,
        offset=offset,
    )
    objects = [ObjectMetadata.model_validate(row) for row in rows]
    return ObjectListResponse(objects=objects, count=len(objects))


@router.get("/providers/{provider_id}/objects/metadata", response_model=ObjectMetadata)
@router.get("/objects/metadata", response_model=ObjectMetadata)
def object_metadata(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
    provider_id: str | None = None,
) -> ObjectMetadata:
    try:
        provider = _provider_or_error(provider_id)
        metadata = provider.get_object_metadata(bucket=bucket, key=key)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to read object metadata: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ObjectMetadata(
        provider=_provider_key(provider),
        bucket=bucket,
        indexed_at=metadata.last_modified,
        **metadata.model_dump(),
    )


@router.get("/providers/{provider_id}/objects/preview", response_model=ObjectPreviewResponse)
@router.get("/objects/preview", response_model=ObjectPreviewResponse)
def object_preview(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
    max_bytes: int = Query(default=1024 * 1024, ge=1024, le=5 * 1024 * 1024),
    provider_id: str | None = None,
) -> ObjectPreviewResponse:
    try:
        provider = _provider_or_error(provider_id)
        preview = provider.get_object_preview(bucket=bucket, key=key, max_bytes=max_bytes)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to create object preview: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ObjectPreviewResponse.model_validate(preview.model_dump())


@router.delete("/providers/{provider_id}/objects", response_model=DeleteObjectResponse)
@router.delete("/objects", response_model=DeleteObjectResponse)
def delete_object(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
    provider_id: str | None = None,
) -> DeleteObjectResponse:
    try:
        provider = _provider_or_error(provider_id)
        result = provider.delete_object(bucket=bucket, key=key)
        delete_object_metadata(_provider_key(provider), bucket, key)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to delete object: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DeleteObjectResponse.model_validate(result.model_dump())


@router.delete("/providers/{provider_id}/prefixes", response_model=DeletePrefixResponse)
@router.delete("/prefixes", response_model=DeletePrefixResponse)
def delete_prefix(
    bucket: str = Query(..., min_length=1),
    prefix: str = Query(...),
    provider_id: str | None = None,
) -> DeletePrefixResponse:
    normalized_prefix = prefix.strip()
    if normalized_prefix in {"", "/"}:
        raise HTTPException(status_code=400, detail="Deleting the bucket root is not allowed.")
    if not normalized_prefix.endswith("/"):
        normalized_prefix = f"{normalized_prefix}/"

    try:
        provider = _provider_or_error(provider_id)
        result = provider.delete_prefix(bucket=bucket, prefix=normalized_prefix)
        delete_prefix_metadata(_provider_key(provider), bucket, normalized_prefix)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to delete prefix: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DeletePrefixResponse.model_validate(result.model_dump())


@router.post("/providers/{provider_id}/objects/upload", response_model=UploadObjectResponse)
@router.post("/objects/upload", response_model=UploadObjectResponse)
def upload_object(
    file: Annotated[UploadFile, File(...)],
    bucket: str = Query(..., min_length=1),
    prefix: str = Query(default=""),
    provider_id: str | None = None,
) -> UploadObjectResponse:
    filename = (file.filename or "").replace("\\", "/").split("/")[-1].strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")
    normalized_prefix = prefix.strip("/")
    key = f"{normalized_prefix}/{filename}" if normalized_prefix else filename
    content_type = mimetypes.guess_type(filename)[0] or file.content_type

    try:
        provider = _provider_or_error(provider_id)
        metadata = provider.upload_object(
            bucket=bucket,
            key=key,
            file_obj=file.file,
            content_type=content_type,
        )
        upsert_objects(_provider_key(provider), bucket, [metadata.model_dump()])
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to upload object: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return UploadObjectResponse(
        provider=_provider_key(provider),
        bucket=bucket,
        indexed_at=metadata.last_modified,
        **metadata.model_dump(),
    )


@router.post("/providers/{provider_id}/objects/rename", response_model=ObjectMetadata)
@router.post("/objects/rename", response_model=ObjectMetadata)
def rename_object(payload: RenameObjectRequest, provider_id: str | None = None) -> ObjectMetadata:
    if payload.source_key == payload.target_key:
        raise HTTPException(status_code=400, detail="Source and target keys must be different.")
    try:
        provider = _provider_or_error(provider_id)
        if not payload.overwrite and _object_exists(provider, payload.bucket, payload.target_key):
            raise HTTPException(status_code=409, detail="Target object already exists.")
        return _copy_then_delete(
            provider,
            bucket=payload.bucket,
            source_key=payload.source_key,
            target_key=payload.target_key,
        )
    except HTTPException:
        raise
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error("Failed to rename object", exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/providers/{provider_id}/prefixes/rename", response_model=ObjectOperationSummary)
@router.post("/prefixes/rename", response_model=ObjectOperationSummary)
def rename_prefix(
    payload: RenamePrefixRequest,
    provider_id: str | None = None,
) -> ObjectOperationSummary:
    source_prefix = _normalize_prefix(payload.source_prefix)
    target_prefix = _normalize_prefix(payload.target_prefix)
    if not source_prefix:
        raise HTTPException(status_code=400, detail="Source prefix cannot be empty.")
    if source_prefix == target_prefix:
        raise HTTPException(status_code=400, detail="Source and target prefixes must be different.")

    try:
        provider = _provider_or_error(provider_id)
        source_keys = _list_prefix_objects(provider, payload.bucket, source_prefix)
        plan = _prefix_move_plan(source_prefix, target_prefix, source_keys)
        target_keys = [item[1] for item in plan]
        conflicts = [] if payload.overwrite else _conflicts(provider, payload.bucket, target_keys)
        operation = create_operation("prefix_rename", total=len(plan), message="Renaming prefix...")
        if conflicts:
            update_operation(
                operation.operation_id,
                status="conflict",
                message="Target objects already exist.",
            )
            return ObjectOperationSummary(
                operation_id=operation.operation_id,
                status="conflict",
                total_objects=len(plan),
                conflicts=conflicts,
            )

        moved = 0
        errors: list[str] = []
        for source_key, target_key in plan:
            try:
                _copy_then_delete(provider, payload.bucket, source_key, target_key)
                moved += 1
                update_operation(operation.operation_id, completed=moved)
            except Exception as exc:  # noqa: BLE001 - operation summaries preserve per-object errors.
                errors.append(f"{source_key}: {exc}")
                update_operation(operation.operation_id, failed=len(errors), errors=errors)
        delete_prefix_metadata(_provider_key(provider), payload.bucket, source_prefix)
        update_operation(
            operation.operation_id,
            status="completed" if not errors else "failed",
            completed=moved,
            failed=len(errors),
            message="Prefix rename completed.",
            errors=errors,
        )
        return ObjectOperationSummary(
            operation_id=operation.operation_id,
            status="completed" if not errors else "failed",
            total_objects=len(plan),
            moved_objects=moved,
            errors=errors,
        )
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error("Failed to rename prefix", exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/providers/{provider_id}/objects/move", response_model=ObjectOperationSummary)
@router.post("/objects/move", response_model=ObjectOperationSummary)
def move_objects(
    payload: MoveObjectsRequest,
    provider_id: str | None = None,
) -> ObjectOperationSummary:
    target_prefix = _normalize_prefix(payload.target_prefix)
    if not payload.items:
        raise HTTPException(status_code=400, detail="At least one item is required.")
    try:
        provider = _provider_or_error(provider_id)
        plan = _move_plan_for_items(provider, payload.bucket, payload.items, target_prefix)
        target_keys = [item[1] for item in plan]
        conflicts = [] if payload.overwrite else _conflicts(provider, payload.bucket, target_keys)
        operation = create_operation("move", total=len(plan), message="Moving objects...")
        if conflicts:
            update_operation(
                operation.operation_id,
                status="conflict",
                message="Target objects already exist.",
            )
            return ObjectOperationSummary(
                operation_id=operation.operation_id,
                status="conflict",
                total_objects=len(plan),
                conflicts=conflicts,
            )

        moved = 0
        errors: list[str] = []
        moved_prefixes = {item[2] for item in plan if item[2]}
        for source_key, target_key, _source_prefix in plan:
            try:
                _copy_then_delete(provider, payload.bucket, source_key, target_key)
                moved += 1
                update_operation(operation.operation_id, completed=moved)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source_key}: {exc}")
                update_operation(operation.operation_id, failed=len(errors), errors=errors)
        for source_prefix in moved_prefixes:
            delete_prefix_metadata(_provider_key(provider), payload.bucket, source_prefix)
        update_operation(
            operation.operation_id,
            status="completed" if not errors else "failed",
            completed=moved,
            failed=len(errors),
            message="Move completed.",
            errors=errors,
        )
        return ObjectOperationSummary(
            operation_id=operation.operation_id,
            status="completed" if not errors else "failed",
            total_objects=len(plan),
            moved_objects=moved,
            errors=errors,
        )
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error("Failed to move objects", exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/providers/{provider_id}/prefixes/merge", response_model=MergePrefixesResponse)
@router.post("/prefixes/merge", response_model=MergePrefixesResponse)
def merge_prefixes(
    payload: MergePrefixesRequest,
    provider_id: str | None = None,
) -> MergePrefixesResponse:
    source_prefix = _normalize_prefix(payload.source_prefix)
    target_prefix = _normalize_prefix(payload.target_prefix)
    strategy = payload.conflict_strategy
    if strategy not in {"fail", "skip", "overwrite"}:
        raise HTTPException(
            status_code=400,
            detail="Conflict strategy must be fail, skip, or overwrite.",
        )
    if not source_prefix:
        raise HTTPException(status_code=400, detail="Source prefix cannot be empty.")
    if source_prefix == target_prefix:
        raise HTTPException(status_code=400, detail="Source and target prefixes must be different.")

    try:
        provider = _provider_or_error(provider_id)
        source_keys = _list_prefix_objects(provider, payload.bucket, source_prefix)
        plan = _prefix_move_plan(source_prefix, target_prefix, source_keys)
        conflicts = _conflicts(provider, payload.bucket, [item[1] for item in plan])
        operation = create_operation("prefix_merge", total=len(plan), message="Merging prefixes...")
        if conflicts and strategy == "fail":
            update_operation(
                operation.operation_id,
                status="conflict",
                message="Merge conflicts found.",
            )
            return MergePrefixesResponse(
                operation_id=operation.operation_id,
                status="conflict",
                source_prefix=source_prefix,
                target_prefix=target_prefix,
                total_objects=len(plan),
                conflicts=conflicts,
            )

        conflict_set = set(conflicts)
        moved = 0
        skipped = 0
        errors: list[str] = []
        for source_key, target_key in plan:
            if strategy == "skip" and target_key in conflict_set:
                skipped += 1
                continue
            try:
                _copy_then_delete(provider, payload.bucket, source_key, target_key)
                moved += 1
                update_operation(operation.operation_id, completed=moved)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{source_key}: {exc}")
                update_operation(operation.operation_id, failed=len(errors), errors=errors)
        if skipped == 0:
            delete_prefix_metadata(_provider_key(provider), payload.bucket, source_prefix)
        update_operation(
            operation.operation_id,
            status="completed" if not errors else "failed",
            completed=moved,
            failed=len(errors),
            message="Merge completed.",
            errors=errors,
        )
        return MergePrefixesResponse(
            operation_id=operation.operation_id,
            status="completed" if not errors else "failed",
            source_prefix=source_prefix,
            target_prefix=target_prefix,
            total_objects=len(plan),
            moved_objects=moved,
            skipped_objects=skipped,
            conflicts=conflicts if strategy == "skip" else [],
            errors=errors,
        )
    except (BotoCoreError, ClientError) as exc:
        raise _storage_error("Failed to merge prefixes", exc) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/operations/{operation_id}", response_model=OperationStatus)
def operation_status(operation_id: str) -> OperationStatus:
    operation = get_operation(operation_id)
    if operation is None:
        raise HTTPException(status_code=404, detail="Operation not found.")
    return operation


@router.get(
    "/providers/{provider_id}/objects/presign-download",
    response_model=PresignDownloadResponse,
)
@router.get("/objects/presign-download", response_model=PresignDownloadResponse)
def presign_download(
    bucket: str = Query(..., min_length=1),
    key: str = Query(..., min_length=1),
    provider_id: str | None = None,
) -> PresignDownloadResponse:
    try:
        provider = _provider_or_error(provider_id)
        url = provider.get_presigned_download_url(bucket=bucket, key=key)
    except (BotoCoreError, ClientError) as exc:
        detail = f"Failed to create download URL: {exc}"
        raise HTTPException(status_code=502, detail=detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PresignDownloadResponse(bucket=bucket, key=key, url=url)
