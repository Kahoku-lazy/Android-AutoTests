import os

import pytest

from django.db.backends.signals import connection_created


def _register_mysql_collation(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_collation("utf8mb4_bin", lambda a, b: (a > b) - (a < b))


connection_created.connect(_register_mysql_collation)

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8766")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL
