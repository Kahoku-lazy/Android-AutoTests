import pytest

from backend.apps.device_pool.manager import reset_status_sync_cache


@pytest.fixture(autouse=True)
def _reset_device_status_cache():
    reset_status_sync_cache()
    yield
    reset_status_sync_cache()
