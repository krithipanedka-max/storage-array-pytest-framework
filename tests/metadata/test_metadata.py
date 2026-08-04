import pytest

pytestmark = [pytest.mark.metadata, pytest.mark.regression]


def test_set_and_get_volume_metadata(storage, default_volume):
    expected = {"owner": "qa", "environment": "automation", "ticket": "STOR-1001"}
    assert storage.metadata.set("volume", default_volume.id, expected) == expected
    assert storage.metadata.get("volume", default_volume.id) == expected


def test_metadata_update_is_non_destructive(storage, default_volume):
    storage.metadata.set("volume", default_volume.id, {"owner": "qa", "env": "dev"})
    updated = storage.metadata.set("volume", default_volume.id, {"env": "test"})
    assert updated == {"owner": "qa", "env": "test"}


def test_delete_single_metadata_key(storage, default_volume):
    storage.metadata.set("volume", default_volume.id, {"owner": "qa", "temporary": "true"})
    result = storage.metadata.delete_key("volume", default_volume.id, "temporary")
    assert result == {"owner": "qa"}


def test_snapshot_metadata_is_independent(storage, seeded_volume, resource_name):
    snapshot = storage.snapshots.create(seeded_volume.id, resource_name("snapshot"))
    storage.metadata.set("volume", seeded_volume.id, {"type": "source"})
    storage.metadata.set("snapshot", snapshot.id, {"type": "backup"})
    assert storage.metadata.get("snapshot", snapshot.id)["type"] == "backup"
    assert storage.metadata.get("volume", seeded_volume.id)["type"] == "source"
