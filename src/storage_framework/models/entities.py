from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Volume:
    id: str
    name: str
    size_gib: int
    pool: str
    raid_group_id: str | None = None
    status: str = "online"
    metadata: dict[str, str] = field(default_factory=dict)
    mapped_hosts: set[str] = field(default_factory=set)
    checksum: str = "empty"


@dataclass(slots=True)
class RaidGroup:
    id: str
    name: str
    level: str
    disks: list[str]
    stripe_kib: int
    status: str = "optimal"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ReplicationSession:
    id: str
    source_volume_id: str
    target_array: str
    mode: str
    rpo_seconds: int
    state: str = "synchronized"
    last_sync_checksum: str = "empty"


@dataclass(slots=True)
class Snapshot:
    id: str
    name: str
    source_volume_id: str
    checksum: str
    status: str = "ready"
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class Clone:
    id: str
    name: str
    source_id: str
    source_type: str
    volume_id: str
    status: str = "online"


@dataclass(slots=True)
class Zone:
    id: str
    name: str
    initiators: list[str]
    targets: list[str]
    active: bool = False


@dataclass(slots=True)
class Host:
    id: str
    name: str
    initiators: list[str]
    paths: list[dict[str, Any]] = field(default_factory=list)
