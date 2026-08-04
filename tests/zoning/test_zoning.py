import pytest

from storage_framework.core.exceptions import ValidationError

pytestmark = [pytest.mark.zoning, pytest.mark.regression]


def test_create_single_initiator_zone(storage, framework_config, resource_name):
    r = framework_config.raw["resources"]
    zone = storage.zoning.create(resource_name("zone"), [r["fc_wwpns"][0]], [r["target_ports"][0]])
    assert len(zone.initiators) == 1
    assert len(zone.targets) == 1

@pytest.mark.smoke
def test_activate_zone(storage, framework_config, resource_name):
    r = framework_config.raw["resources"]
    zone = storage.zoning.create(resource_name("zone"), r["fc_wwpns"], r["target_ports"])
    assert storage.zoning.activate(zone.id).active is True


def test_zone_requires_both_member_types(storage, resource_name):
    with pytest.raises(ValidationError):
        storage.zoning.create(resource_name("zone"), [], ["target-1"])
