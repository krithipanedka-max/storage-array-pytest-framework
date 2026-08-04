import pytest

pytestmark = [pytest.mark.snapshot, pytest.mark.replication, pytest.mark.regression]


def test_snapshot_creation_still_works_during_failover(storage, seeded_volume, framework_config, resource_name):
    replication_cfg = framework_config.raw["replication"]
    session = storage.replication.create(
        source_volume_id=seeded_volume.id,
        target_array=replication_cfg["peer_array"],
        mode="sync",
        rpo_seconds=0,
    )

    assert storage.replication.failover(session.id).state == "failed_over"

    snapshot = storage.snapshots.create(seeded_volume.id, resource_name("snapshot"))

    assert snapshot.status == "ready"
    assert snapshot.checksum == seeded_volume.checksum
    assert storage.snapshots.get(snapshot.id).checksum == seeded_volume.checksum
