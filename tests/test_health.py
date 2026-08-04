import pytest


@pytest.mark.smoke
def test_array_health_is_healthy(adapter):
    health = adapter.health()
    assert health["status"] == "healthy"
    assert health["controllers"] >= 2
