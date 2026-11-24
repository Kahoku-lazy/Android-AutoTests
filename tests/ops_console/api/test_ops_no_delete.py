from __future__ import annotations

import pytest

from django.urls import Resolver404, resolve

pytestmark = [pytest.mark.api]


@pytest.mark.parametrize(
    "path",
    [
        "/api/ops/users/",
        "/api/ops/users/1/",
        "/api/ops/users/1/delete/",
    ],
)
def test_delete_requests_have_no_route(path: str):
    if path == "/api/ops/users/":
        assert resolve(path) is not None
        return
    with pytest.raises(Resolver404):
        resolve(path)


def test_purge_is_the_only_delete_route():
    assert resolve("/api/ops/users/purge/") is not None
    with pytest.raises(Resolver404):
        resolve("/api/ops/users/1/purge/")
