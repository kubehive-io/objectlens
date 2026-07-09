from sqlalchemy import create_engine

from app import db
from app.routers import buckets


class FakeProvider:
    provider = "ceph"

    def list_objects(self, *args, **kwargs):  # pragma: no cover - test should use index
        raise AssertionError("indexed prefix should not call provider")


def test_prefix_browsing_returns_common_prefixes_and_direct_children(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    monkeypatch.setattr(db, "get_engine", lambda: engine)
    db.metadata.create_all(engine)

    db.upsert_objects(
        "ceph",
        "bucket",
        [
            {"key": "foo.txt", "size": 1},
            {"key": "logs/2026/01/file.json", "size": 2},
            {"key": "logs/2026/02/file.json", "size": 3},
            {"key": "logs/readme.txt", "size": 4},
        ],
    )

    root_objects = db.direct_child_objects("ceph", "bucket", prefix="", delimiter="/")
    root_prefixes = db.common_prefixes("ceph", "bucket", prefix="", delimiter="/")

    assert [row["key"] for row in root_objects] == ["foo.txt"]
    assert root_prefixes == [{"name": "logs/", "prefix": "logs/", "object_count": 3}]

    logs_objects = db.direct_child_objects("ceph", "bucket", prefix="logs/", delimiter="/")
    logs_prefixes = db.common_prefixes("ceph", "bucket", prefix="logs/", delimiter="/")

    assert [row["key"] for row in logs_objects] == ["logs/readme.txt"]
    assert logs_prefixes == [{"name": "2026/", "prefix": "logs/2026/", "object_count": 2}]


def test_scoped_glob_search_returns_current_level_items(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    monkeypatch.setattr(db, "get_engine", lambda: engine)
    monkeypatch.setattr(buckets, "get_engine", lambda: engine, raising=False)
    monkeypatch.setattr(buckets, "get_provider", lambda settings: FakeProvider())
    db.metadata.create_all(engine)

    db.upsert_objects(
        "ceph",
        "bucket",
        [
            {"key": "reports/2026/july/customer-billing-export.json", "size": 2},
            {"key": "reports/2026/invoice-billing-root.json", "size": 3},
            {"key": "reports/2025/old-billing.json", "size": 4},
        ],
    )
    db.mark_prefix_indexed("ceph", "bucket", "reports/2026/")

    result = buckets.bucket_objects(
        bucket="bucket",
        prefix="reports/2026/",
        search="*-billing-*",
        limit=50,
        offset=0,
        delimiter="/",
    )

    assert [(item.type, item.name) for item in result.items] == [
        ("prefix", "july/"),
        ("object", "invoice-billing-root.json"),
    ]


def test_delete_metadata_helpers_remove_objects_and_prefixes(monkeypatch) -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    monkeypatch.setattr(db, "get_engine", lambda: engine)
    db.metadata.create_all(engine)

    db.upsert_objects(
        "ceph",
        "bucket",
        [
            {"key": "logs/2026/file.json", "size": 2},
            {"key": "logs/2027/file.json", "size": 3},
            {"key": "keep.txt", "size": 4},
        ],
    )
    db.upsert_prefixes(
        "ceph",
        "bucket",
        "",
        [{"name": "logs/", "prefix": "logs/", "object_count": 2}],
    )
    db.mark_prefix_indexed("ceph", "bucket", "logs/")

    assert db.delete_prefix_metadata("ceph", "bucket", "logs/") == 2

    remaining = db.search_objects("ceph", "bucket", limit=10)
    assert [row["key"] for row in remaining] == ["keep.txt"]
    assert db.indexed_common_prefixes("ceph", "bucket", "") == []
