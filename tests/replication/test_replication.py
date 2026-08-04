import pytest

from storage_framework.core.exceptions import ResourceConflict, ValidationError

pytestmark = [pytest.mark.replication, pytest.mark.regression]


def test_create_async_replication(storage, seeded_volume, framework_config):
    cfg = framework_config.raw["replication"]
    session = storage.replication.create(source_volume_id=seeded_volume.id, target_array=cfg["peer_array"], mode="async", rpo_seconds=cfg["rpo_seconds"])
    assert session.state == "synchronized"
    assert session.last_sync_checksum == seeded_volume.checksum


def test_incremental_sync_updates_checksum(storage, seeded_volume):
    session = storage.replication.create(source_volume_id=seeded_volume.id, target_array="dr", mode="async", rpo_seconds=300)
    new_checksum = storage.volumes.write_pattern(seeded_volume.id, "changed-data")
    synced = storage.replication.sync(session.id)
    assert synced.last_sync_checksum == new_checksum

@pytest.mark.smoke
def test_failover_and_failback(storage, seeded_volume):
    session = storage.replication.create(source_volume_id=seeded_volume.id, target_array="dr", mode="sync", rpo_seconds=0)
    assert storage.replication.failover(session.id).state == "failed_over"
    assert storage.replication.failback(session.id).state == "synchronized"


def test_failback_rejected_before_failover(storage, seeded_volume):
    session = storage.replication.create(source_volume_id=seeded_volume.id, target_array="dr", mode="async", rpo_seconds=60)
    with pytest.raises(ResourceConflict):
        storage.replication.failback(session.id)


def test_invalid_replication_mode_rejected(storage, seeded_volume):
    with pytest.raises(ValidationError):
        storage.replication.create(source_volume_id=seeded_volume.id, target_array="dr", mode="invalid", rpo_seconds=60)
