from __future__ import annotations

import re

import pytest
import yaml

from django.contrib.staticfiles.views import serve
from django.test import Client, RequestFactory
from django.urls import Resolver404, resolve

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

REMOVED_DOC_PATHS = ["/api/docs", "/api/docs.html"]
KEPT_DOC_PATHS = ["/api/schema/", "/api/swagger/"]

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

THIRD_PARTY_ASSET = re.compile(r"""(?:src|href)=["']https?://[^"']+["']""")
SAME_ORIGIN_ASSET = re.compile(r"""(?:src|href)=["'](/static/[^"']+)["']""")


@pytest.fixture
def client():
    return Client()


def test_removed_handwritten_doc_paths_are_gone(client):
    for path in REMOVED_DOC_PATHS:
        with pytest.raises(Resolver404):
            resolve(path)
        assert client.get(path).status_code == 401, path


def test_kept_doc_endpoints_stay_public(client):
    for path in KEPT_DOC_PATHS:
        assert client.get(path).status_code == 200, path


def _load_schema(client) -> dict:
    resp = client.get("/api/schema/")
    assert resp.status_code == 200
    return yaml.safe_load(resp.content.decode("utf-8"))


def test_every_operation_has_a_description(client):
    schema = _load_schema(client)
    missing = [
        f"{method.upper()} {path}"
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
        if method in HTTP_METHODS and not (operation.get("description") or operation.get("summary"))
    ]
    assert missing == [], f"缺少说明的端点: {missing}"


def test_every_tag_has_a_chinese_description(client):
    schema = _load_schema(client)
    tags = schema.get("tags") or []
    assert tags, "schema 未声明任何 tag 说明（SPECTACULAR_SETTINGS['TAGS'] 缺失？）"
    undocumented = [tag["name"] for tag in tags if not (tag.get("description") or "").strip()]
    assert undocumented == [], f"缺少说明的分组: {undocumented}"


def test_swagger_ui_has_no_third_party_assets(client):
    html = client.get("/api/swagger/").content.decode("utf-8")
    external = THIRD_PARTY_ASSET.findall(html)
    assert external == [], f"文档页仍引用外部资源: {external}"


def test_swagger_ui_assets_are_served_same_origin(client):
    html = client.get("/api/swagger/").content.decode("utf-8")
    assets = sorted(set(SAME_ORIGIN_ASSET.findall(html)))
    assert assets, "文档页未引用任何同源静态资产（SWAGGER_UI_DIST=SIDECAR 未生效？）"

    factory = RequestFactory()
    for asset in assets:
        relative_path = asset.removeprefix("/static/")
        response = serve(factory.get(asset), relative_path, insecure=True)
        assert response.status_code == 200, f"静态资产不可取: {asset}"
