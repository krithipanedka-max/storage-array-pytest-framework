from __future__ import annotations

import logging
from pathlib import Path

import pytest

from storage_framework.adapters.simulator import SimulatorAdapter
from storage_framework.clients.facade import StorageClient
from storage_framework.core.config import FrameworkConfig, load_config
from storage_framework.utils.naming import unique_name

LOG = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("storage-array")
    group.addoption("--config", action="store", default="config/lab.yaml", help="Path to YAML configuration")
    group.addoption("--backend", action="store", default=None, help="Override backend from YAML")
    group.addoption("--run-destructive", action="store_true", default=False, help="Enable destructive tests")
    group.addoption("--keep-resources", action="store_true", default=False, help="Do not clean simulator resources")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-destructive"):
        return
    skip = pytest.mark.skip(reason="requires --run-destructive")
    for item in items:
        if "destructive" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def framework_config(pytestconfig: pytest.Config) -> FrameworkConfig:
    return load_config(pytestconfig.getoption("--config"))


@pytest.fixture(scope="session")
def backend_name(pytestconfig: pytest.Config, framework_config: FrameworkConfig) -> str:
    return pytestconfig.getoption("--backend") or framework_config.backend


def _build_adapter(backend: str, config: FrameworkConfig):
    if backend == "simulator":
        return SimulatorAdapter(config.raw.get("array", {}).get("name", "sim-array"))
    if backend == "rest":
        pytest.skip("REST adapter is a vendor implementation template; implement it before use")
    raise pytest.UsageError(f"Unknown backend: {backend}")


@pytest.fixture(scope="session")
def adapter(backend_name: str, framework_config: FrameworkConfig):
    instance = _build_adapter(backend_name, framework_config)
    health = instance.health()
    assert health["status"] == "healthy", f"Array health check failed: {health}"
    yield instance


@pytest.fixture(scope="session")
def storage(adapter) -> StorageClient:
    return StorageClient(adapter)


@pytest.fixture
def resource_name(framework_config: FrameworkConfig):
    return lambda feature: unique_name(framework_config.prefix, feature)


@pytest.fixture(autouse=True)
def isolated_simulator(adapter, pytestconfig: pytest.Config):
    if isinstance(adapter, SimulatorAdapter):
        adapter.reset()
    yield
    if isinstance(adapter, SimulatorAdapter) and not pytestconfig.getoption("--keep-resources"):
        adapter.reset()


@pytest.fixture
def default_volume(storage: StorageClient, framework_config: FrameworkConfig, resource_name):
    resources = framework_config.raw["resources"]
    return storage.volumes.create(
        name=resource_name("volume"),
        size_gib=resources["default_volume_size_gib"],
        pool=resources["pool_name"],
    )


@pytest.fixture
def seeded_volume(storage: StorageClient, default_volume):
    checksum = storage.volumes.write_pattern(default_volume.id, "pytest-storage-pattern-v1")
    assert checksum == storage.volumes.get(default_volume.id).checksum
    return default_volume


@pytest.fixture
def default_host(storage: StorageClient, framework_config: FrameworkConfig, resource_name):
    initiators = framework_config.raw["resources"]["initiators"]
    return storage.multipath.create_host(resource_name("host"), initiators)
