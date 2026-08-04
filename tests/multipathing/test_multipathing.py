import pytest

from storage_framework.core.exceptions import ResourceConflict

pytestmark = [pytest.mark.multipathing, pytest.mark.regression]


@pytest.mark.smoke
def test_volume_has_redundant_paths(storage, default_volume, default_host):
    host = storage.multipath.map_volume(default_volume.id, default_host.id, path_count=2)
    assert len(host.paths) == 2
    assert {p["state"] for p in host.paths} == {"active", "standby"}


def test_path_failure_promotes_alternate_path(storage, default_volume, default_host):
    host = storage.multipath.map_volume(default_volume.id, default_host.id, path_count=2)
    active = next(p for p in host.paths if p["state"] == "active")
    updated = storage.multipath.set_path_state(host.id, active["id"], "failed")
    assert any(p["state"] == "active" and p["id"] != active["id"] for p in updated.paths)


def test_unmap_removes_paths_and_mapping(storage, default_volume, default_host):
    storage.multipath.map_volume(default_volume.id, default_host.id, path_count=4)
    storage.multipath.unmap_volume(default_volume.id, default_host.id)
    assert storage.multipath.get_host(default_host.id).paths == []
    assert default_host.id not in storage.volumes.get(default_volume.id).mapped_hosts

@pytest.mark.destructive
def test_mapped_host_cannot_be_deleted(storage, default_volume, default_host):
    storage.multipath.map_volume(default_volume.id, default_host.id)
    with pytest.raises(ResourceConflict):
        storage.multipath.delete_host(default_host.id)
