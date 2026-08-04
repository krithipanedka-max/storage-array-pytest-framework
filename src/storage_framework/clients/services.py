from __future__ import annotations

from storage_framework.core.adapter import StorageArrayAdapter


class BaseService:
    def __init__(self, adapter: StorageArrayAdapter) -> None:
        self.adapter = adapter


class RaidService(BaseService):
    create = lambda self, **kwargs: self.adapter.create_raid_group(**kwargs)
    get = lambda self, resource_id: self.adapter.get_raid_group(resource_id)
    delete = lambda self, resource_id: self.adapter.delete_raid_group(resource_id)


class VolumeService(BaseService):
    create = lambda self, **kwargs: self.adapter.create_volume(**kwargs)
    get = lambda self, resource_id: self.adapter.get_volume(resource_id)
    delete = lambda self, resource_id: self.adapter.delete_volume(resource_id)
    write_pattern = lambda self, volume_id, pattern: self.adapter.write_pattern(volume_id, pattern)


class ReplicationService(BaseService):
    create = lambda self, **kwargs: self.adapter.create_replication(**kwargs)
    get = lambda self, resource_id: self.adapter.get_replication(resource_id)
    sync = lambda self, resource_id: self.adapter.sync_replication(resource_id)
    failover = lambda self, resource_id: self.adapter.failover_replication(resource_id)
    failback = lambda self, resource_id: self.adapter.failback_replication(resource_id)
    delete = lambda self, resource_id: self.adapter.delete_replication(resource_id)


class SnapshotService(BaseService):
    create = lambda self, volume_id, name: self.adapter.create_snapshot(volume_id, name)
    get = lambda self, resource_id: self.adapter.get_snapshot(resource_id)
    restore = lambda self, resource_id: self.adapter.restore_snapshot(resource_id)
    delete = lambda self, resource_id: self.adapter.delete_snapshot(resource_id)


class CloneService(BaseService):
    create = lambda self, source_id, source_type, name: self.adapter.create_clone(source_id, source_type, name)
    get = lambda self, resource_id: self.adapter.get_clone(resource_id)
    split = lambda self, resource_id: self.adapter.split_clone(resource_id)
    delete = lambda self, resource_id: self.adapter.delete_clone(resource_id)


class ZoningService(BaseService):
    create = lambda self, name, initiators, targets: self.adapter.create_zone(name, initiators, targets)
    activate = lambda self, resource_id: self.adapter.activate_zone(resource_id)
    get = lambda self, resource_id: self.adapter.get_zone(resource_id)
    delete = lambda self, resource_id: self.adapter.delete_zone(resource_id)


class MultipathService(BaseService):
    create_host = lambda self, name, initiators: self.adapter.create_host(name, initiators)
    map_volume = lambda self, volume_id, host_id, path_count=2: self.adapter.map_volume(volume_id, host_id, path_count)
    get_host = lambda self, resource_id: self.adapter.get_host(resource_id)
    set_path_state = lambda self, host_id, path_id, state: self.adapter.set_path_state(host_id, path_id, state)
    unmap_volume = lambda self, volume_id, host_id: self.adapter.unmap_volume(volume_id, host_id)
    delete_host = lambda self, resource_id: self.adapter.delete_host(resource_id)


class MetadataService(BaseService):
    set = lambda self, resource_type, resource_id, values: self.adapter.set_metadata(resource_type, resource_id, values)
    get = lambda self, resource_type, resource_id: self.adapter.get_metadata(resource_type, resource_id)
    delete_key = lambda self, resource_type, resource_id, key: self.adapter.delete_metadata_key(resource_type, resource_id, key)
