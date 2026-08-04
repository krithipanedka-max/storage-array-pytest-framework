import pytest

pytestmark = [pytest.mark.clone, pytest.mark.regression]


def test_clone_from_volume_has_identical_data(storage, seeded_volume, resource_name):
    clone = storage.clones.create(seeded_volume.id, "volume", resource_name("clone"))
    clone_volume = storage.volumes.get(clone.volume_id)
    assert clone_volume.checksum == seeded_volume.checksum


def test_clone_from_snapshot_has_snapshot_data(storage, seeded_volume, resource_name):
    snapshot = storage.snapshots.create(seeded_volume.id, resource_name("snapshot"))
    storage.volumes.write_pattern(seeded_volume.id, "later-data")
    clone = storage.clones.create(snapshot.id, "snapshot", resource_name("clone"))
    assert storage.volumes.get(clone.volume_id).checksum == snapshot.checksum


def test_split_clone_becomes_independent(storage, seeded_volume, resource_name):
    clone = storage.clones.create(seeded_volume.id, "volume", resource_name("clone"))
    assert storage.clones.split(clone.id).status == "independent"

@pytest.mark.destructive
def test_delete_clone_removes_clone_volume(storage, seeded_volume, resource_name):
    clone = storage.clones.create(seeded_volume.id, "volume", resource_name("clone"))
    storage.clones.delete(clone.id)
    with pytest.raises(Exception):
        storage.volumes.get(clone.volume_id)
