from __future__ import annotations

from storage_framework.clients.services import (
    CloneService, MetadataService, MultipathService, RaidService, ReplicationService,
    SnapshotService, VolumeService, ZoningService,
)
from storage_framework.core.adapter import StorageArrayAdapter


class StorageClient:
    def __init__(self, adapter: StorageArrayAdapter) -> None:
        self.adapter = adapter
        self.raid = RaidService(adapter)
        self.volumes = VolumeService(adapter)
        self.replication = ReplicationService(adapter)
        self.snapshots = SnapshotService(adapter)
        self.clones = CloneService(adapter)
        self.zoning = ZoningService(adapter)
        self.multipath = MultipathService(adapter)
        self.metadata = MetadataService(adapter)
