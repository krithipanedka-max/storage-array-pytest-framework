import pytest

pytestmark = [pytest.mark.integration, pytest.mark.regression]


def test_protected_volume_lifecycle(storage, framework_config, resource_name):
    r = framework_config.raw["resources"]
    rg = storage.raid.create(name=resource_name("raid5"), level="5", disks=["d1", "d2", "d3"], stripe_kib=256)
    volume = storage.volumes.create(name=resource_name("volume"), size_gib=10, pool=r["pool_name"], raid_group_id=rg.id)
    checksum = storage.volumes.write_pattern(volume.id, "business-data-v1")
    storage.metadata.set("volume", volume.id, {"app": "database", "protection": "gold"})
    snapshot = storage.snapshots.create(volume.id, resource_name("snapshot"))
    clone = storage.clones.create(snapshot.id, "snapshot", resource_name("clone"))
    replication = storage.replication.create(source_volume_id=volume.id, target_array="dr-array", mode="async", rpo_seconds=300)
    zone = storage.zoning.create(resource_name("zone"), [r["fc_wwpns"][0]], r["target_ports"])
    storage.zoning.activate(zone.id)
    host = storage.multipath.create_host(resource_name("host"), r["initiators"])
    storage.multipath.map_volume(volume.id, host.id, path_count=2)

    assert snapshot.checksum == checksum
    assert storage.volumes.get(clone.volume_id).checksum == checksum
    assert replication.last_sync_checksum == checksum
    assert storage.zoning.get(zone.id).active
    assert len(storage.multipath.get_host(host.id).paths) == 2
    assert storage.metadata.get("volume", volume.id)["protection"] == "gold"
