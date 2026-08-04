import pytest

from storage_framework.core.exceptions import ResourceConflict, ValidationError

pytestmark = [pytest.mark.raid, pytest.mark.regression]


@pytest.mark.parametrize("level,disks", [("1", ["d1", "d2"]), ("5", ["d1", "d2", "d3"]), ("6", ["d1", "d2", "d3", "d4"]), ("10", ["d1", "d2", "d3", "d4"])])
def test_create_supported_raid_levels(storage, resource_name, level, disks):
    rg = storage.raid.create(name=resource_name(f"raid{level}"), level=level, disks=disks, stripe_kib=256)
    assert storage.raid.get(rg.id).status == "optimal"
    assert rg.level == level


def test_reject_insufficient_disks(storage, resource_name):
    with pytest.raises(ValidationError):
        storage.raid.create(name=resource_name("raid6"), level="6", disks=["d1", "d2", "d3"], stripe_kib=256)


def test_volume_can_be_created_on_raid_group(storage, resource_name):
    rg = storage.raid.create(name=resource_name("raid5"), level="5", disks=["d1", "d2", "d3"], stripe_kib=128)
    volume = storage.volumes.create(name=resource_name("volume"), size_gib=20, pool="pool-a", raid_group_id=rg.id)
    assert volume.raid_group_id == rg.id

@pytest.mark.destructive
def test_raid_group_with_volume_cannot_be_deleted(storage, resource_name):
    rg = storage.raid.create(name=resource_name("raid1"), level="1", disks=["d1", "d2"], stripe_kib=64)
    storage.volumes.create(name=resource_name("volume"), size_gib=1, pool="pool-a", raid_group_id=rg.id)
    with pytest.raises(ResourceConflict):
        storage.raid.delete(rg.id)
