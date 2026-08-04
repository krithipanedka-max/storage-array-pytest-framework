from __future__ import annotations

import hashlib
import itertools
from dataclasses import replace
from typing import Any

from storage_framework.core.adapter import StorageArrayAdapter
from storage_framework.core.exceptions import ResourceConflict, ResourceNotFound, ValidationError
from storage_framework.models import Clone, Host, RaidGroup, ReplicationSession, Snapshot, Volume, Zone


class SimulatorAdapter(StorageArrayAdapter):
    """Deterministic in-memory storage array used for framework and CI validation."""

    def __init__(self, array_name: str = "sim-array") -> None:
        self.array_name = array_name
        self._ids = itertools.count(1)
        self.reset()

    def _id(self, prefix: str) -> str:
        return f"{prefix}-{next(self._ids):05d}"

    @staticmethod
    def _require(store: dict[str, Any], resource_id: str) -> Any:
        try:
            return store[resource_id]
        except KeyError as exc:
            raise ResourceNotFound(resource_id) from exc

    def health(self) -> dict[str, Any]:
        return {"name": self.array_name, "status": "healthy", "controllers": 2}

    def reset(self) -> None:
        self.raid_groups: dict[str, RaidGroup] = {}
        self.volumes: dict[str, Volume] = {}
        self.replications: dict[str, ReplicationSession] = {}
        self.snapshots: dict[str, Snapshot] = {}
        self.clones: dict[str, Clone] = {}
        self.zones: dict[str, Zone] = {}
        self.hosts: dict[str, Host] = {}

    def create_raid_group(self, name: str, level: str, disks: list[str], stripe_kib: int) -> RaidGroup:
        minimum = {"0": 2, "1": 2, "5": 3, "6": 4, "10": 4}
        if level not in minimum:
            raise ValidationError(f"Unsupported RAID level: {level}")
        if len(disks) < minimum[level] or len(set(disks)) != len(disks):
            raise ValidationError("Invalid disk count or duplicate disk")
        rg = RaidGroup(self._id("rg"), name, level, list(disks), stripe_kib)
        self.raid_groups[rg.id] = rg
        return rg

    def get_raid_group(self, resource_id: str) -> RaidGroup:
        return self._require(self.raid_groups, resource_id)

    def delete_raid_group(self, resource_id: str) -> None:
        self._require(self.raid_groups, resource_id)
        if any(v.raid_group_id == resource_id for v in self.volumes.values()):
            raise ResourceConflict("RAID group contains volumes")
        del self.raid_groups[resource_id]

    def create_volume(self, name: str, size_gib: int, pool: str, raid_group_id: str | None = None) -> Volume:
        if size_gib <= 0:
            raise ValidationError("Volume size must be positive")
        if raid_group_id:
            self.get_raid_group(raid_group_id)
        vol = Volume(self._id("vol"), name, size_gib, pool, raid_group_id)
        self.volumes[vol.id] = vol
        return vol

    def get_volume(self, resource_id: str) -> Volume:
        return self._require(self.volumes, resource_id)

    def delete_volume(self, resource_id: str) -> None:
        volume = self.get_volume(resource_id)
        if volume.mapped_hosts:
            raise ResourceConflict("Volume is mapped")
        del self.volumes[resource_id]

    def write_pattern(self, volume_id: str, pattern: str) -> str:
        volume = self.get_volume(volume_id)
        volume.checksum = hashlib.sha256(pattern.encode()).hexdigest()
        return volume.checksum

    def create_replication(self, source_volume_id: str, target_array: str, mode: str, rpo_seconds: int) -> ReplicationSession:
        source = self.get_volume(source_volume_id)
        if mode not in {"sync", "async"}:
            raise ValidationError("Replication mode must be sync or async")
        if rpo_seconds < 0:
            raise ValidationError("RPO cannot be negative")
        session = ReplicationSession(self._id("rep"), source.id, target_array, mode, rpo_seconds, last_sync_checksum=source.checksum)
        self.replications[session.id] = session
        return session

    def get_replication(self, resource_id: str) -> ReplicationSession:
        return self._require(self.replications, resource_id)

    def sync_replication(self, resource_id: str) -> ReplicationSession:
        session = self.get_replication(resource_id)
        session.state = "synchronized"
        session.last_sync_checksum = self.get_volume(session.source_volume_id).checksum
        return session

    def failover_replication(self, resource_id: str) -> ReplicationSession:
        session = self.get_replication(resource_id)
        session.state = "failed_over"
        return session

    def failback_replication(self, resource_id: str) -> ReplicationSession:
        session = self.get_replication(resource_id)
        if session.state != "failed_over":
            raise ResourceConflict("Failback requires failed_over state")
        session.state = "synchronized"
        return session

    def delete_replication(self, resource_id: str) -> None:
        self._require(self.replications, resource_id)
        del self.replications[resource_id]

    def create_snapshot(self, volume_id: str, name: str) -> Snapshot:
        source = self.get_volume(volume_id)
        snap = Snapshot(self._id("snap"), name, source.id, source.checksum)
        self.snapshots[snap.id] = snap
        return snap

    def get_snapshot(self, resource_id: str) -> Snapshot:
        return self._require(self.snapshots, resource_id)

    def restore_snapshot(self, snapshot_id: str) -> Volume:
        snap = self.get_snapshot(snapshot_id)
        volume = self.get_volume(snap.source_volume_id)
        volume.checksum = snap.checksum
        return volume

    def delete_snapshot(self, resource_id: str) -> None:
        self._require(self.snapshots, resource_id)
        if any(c.source_id == resource_id and c.source_type == "snapshot" for c in self.clones.values()):
            raise ResourceConflict("Snapshot has dependent clone")
        del self.snapshots[resource_id]

    def create_clone(self, source_id: str, source_type: str, name: str) -> Clone:
        if source_type == "volume":
            source = self.get_volume(source_id)
            checksum, size, pool = source.checksum, source.size_gib, source.pool
        elif source_type == "snapshot":
            snap = self.get_snapshot(source_id)
            original = self.get_volume(snap.source_volume_id)
            checksum, size, pool = snap.checksum, original.size_gib, original.pool
        else:
            raise ValidationError("Clone source_type must be volume or snapshot")
        clone_volume = self.create_volume(name, size, pool)
        clone_volume.checksum = checksum
        clone = Clone(self._id("clone"), name, source_id, source_type, clone_volume.id)
        self.clones[clone.id] = clone
        return clone

    def get_clone(self, resource_id: str) -> Clone:
        return self._require(self.clones, resource_id)

    def split_clone(self, resource_id: str) -> Clone:
        clone = self.get_clone(resource_id)
        clone.status = "independent"
        return clone

    def delete_clone(self, resource_id: str) -> None:
        clone = self.get_clone(resource_id)
        self.volumes.pop(clone.volume_id, None)
        del self.clones[resource_id]

    def create_zone(self, name: str, initiators: list[str], targets: list[str]) -> Zone:
        if not initiators or not targets:
            raise ValidationError("Zone requires initiator and target members")
        zone = Zone(self._id("zone"), name, list(initiators), list(targets))
        self.zones[zone.id] = zone
        return zone

    def activate_zone(self, resource_id: str) -> Zone:
        zone = self.get_zone(resource_id)
        zone.active = True
        return zone

    def get_zone(self, resource_id: str) -> Zone:
        return self._require(self.zones, resource_id)

    def delete_zone(self, resource_id: str) -> None:
        self._require(self.zones, resource_id)
        del self.zones[resource_id]

    def create_host(self, name: str, initiators: list[str]) -> Host:
        if not initiators:
            raise ValidationError("Host requires at least one initiator")
        host = Host(self._id("host"), name, list(initiators))
        self.hosts[host.id] = host
        return host

    def map_volume(self, volume_id: str, host_id: str, path_count: int = 2) -> Host:
        volume, host = self.get_volume(volume_id), self.get_host(host_id)
        if path_count < 1:
            raise ValidationError("path_count must be positive")
        host.paths = [{"id": f"path-{i+1}", "volume_id": volume.id, "state": "active" if i == 0 else "standby"} for i in range(path_count)]
        volume.mapped_hosts.add(host.id)
        return host

    def get_host(self, resource_id: str) -> Host:
        return self._require(self.hosts, resource_id)

    def set_path_state(self, host_id: str, path_id: str, state: str) -> Host:
        host = self.get_host(host_id)
        for path in host.paths:
            if path["id"] == path_id:
                path["state"] = state
                if state == "failed":
                    for alternate in host.paths:
                        if alternate["id"] != path_id and alternate["state"] != "failed":
                            alternate["state"] = "active"
                            break
                return host
        raise ResourceNotFound(path_id)

    def unmap_volume(self, volume_id: str, host_id: str) -> None:
        volume, host = self.get_volume(volume_id), self.get_host(host_id)
        host.paths = [p for p in host.paths if p["volume_id"] != volume_id]
        volume.mapped_hosts.discard(host_id)

    def delete_host(self, resource_id: str) -> None:
        host = self.get_host(resource_id)
        if host.paths:
            raise ResourceConflict("Host has mapped paths")
        del self.hosts[resource_id]

    def _metadata_target(self, resource_type: str, resource_id: str) -> Any:
        stores = {"volume": self.volumes, "snapshot": self.snapshots, "raid_group": self.raid_groups}
        if resource_type not in stores:
            raise ValidationError(f"Metadata unsupported for {resource_type}")
        return self._require(stores[resource_type], resource_id)

    def set_metadata(self, resource_type: str, resource_id: str, values: dict[str, str]) -> dict[str, str]:
        target = self._metadata_target(resource_type, resource_id)
        target.metadata.update({str(k): str(v) for k, v in values.items()})
        return dict(target.metadata)

    def get_metadata(self, resource_type: str, resource_id: str) -> dict[str, str]:
        return dict(self._metadata_target(resource_type, resource_id).metadata)

    def delete_metadata_key(self, resource_type: str, resource_id: str, key: str) -> dict[str, str]:
        target = self._metadata_target(resource_type, resource_id)
        target.metadata.pop(key, None)
        return dict(target.metadata)
