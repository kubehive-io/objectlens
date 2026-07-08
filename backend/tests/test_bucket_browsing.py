from sqlalchemy import create_engine

from app import db


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
