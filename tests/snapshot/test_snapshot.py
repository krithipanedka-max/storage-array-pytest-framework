import pytest

from storage_framework.core.exceptions import ResourceConflict

pytestmark = [pytest.mark.snapshot, pytest.mark.regression]


@pytest.mark.smoke
def test_snapshot_preserves_point_in_time_checksum(storage, seeded_volume, resource_name):
    snapshot = storage.snapshots.create(seeded_volume.id, resource_name("snapshot"))
    assert snapshot.status == "ready"
    assert snapshot.checksum == seeded_volume.checksum


def test_restore_snapshot_recovers_original_data(storage, seeded_volume, resource_name):
    snapshot = storage.snapshots.create(seeded_volume.id, resource_name("snapshot"))
    original = snapshot.checksum
    storage.volumes.write_pattern(seeded_volume.id, "corrupt-or-new-data")
    restored = storage.snapshots.restore(snapshot.id)
    assert restored.checksum == original

@pytest.mark.destructive
def test_snapshot_with_dependent_clone_cannot_be_deleted(storage, seeded_volume, resource_name):
    snapshot = storage.snapshots.create(seeded_volume.id, resource_name("snapshot"))
    storage.clones.create(snapshot.id, "snapshot", resource_name("clone"))
    with pytest.raises(ResourceConflict):
        storage.snapshots.delete(snapshot.id)
