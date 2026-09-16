"""公开 API 文档面契约（`api-docs-surface`）：以 schema + Swagger UI 为唯一文档面。

对照 `openspec/changes/retire-handwritten-api-docs` 的 spec，看守四件事：

1. 已删除的手写文档路径（`/api/docs` / `/api/docs.html`）不再提供文档；
2. 保留的 `/api/schema/` 与 `/api/swagger/` 免 JWT 公开可达；
3. schema 内每个 operation、每个分组（tag）都有中文说明；
4. Swagger UI 页面不引用第三方域名，且引用的静态资产同源可取（离线可用）。

运行：`pytest tests/graybox/unit/test_api_docs_surface.py -v`
"""

from __future__ import annotations

import re

import pytest
import yaml

from django.contrib.staticfiles.views import serve
from django.test import Client, RequestFactory
from django.urls import Resolver404, resolve

# django_db：JWTAuthenticationMiddleware 每请求调用 close_old_connections()
pytestmark = [pytest.mark.django_db, pytest.mark.unit]

REMOVED_DOC_PATHS = ["/api/docs", "/api/docs.html"]
KEPT_DOC_PATHS = ["/api/schema/", "/api/swagger/"]

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")

# 页面里指向第三方域名的资源引用（外链字体 / CDN）
THIRD_PARTY_ASSET = re.compile(r"""(?:src|href)=["']https?://[^"']+["']""")
# 页面里指向本服务的静态资产（sidecar 提供的 Swagger UI 资产）
SAME_ORIGIN_ASSET = re.compile(r"""(?:src|href)=["'](/static/[^"']+)["']""")


@pytest.fixture
def client():
    return Client()


def test_removed_handwritten_doc_paths_are_gone(client):
    """已删除的文档路径不再提供文档：无凭据 401，路由本身也不存在（等价携带凭据时 404）。"""
    for path in REMOVED_DOC_PATHS:
        with pytest.raises(Resolver404):
            resolve(path)
        assert client.get(path).status_code == 401, path


def test_kept_doc_endpoints_stay_public(client):
    """schema 与 swagger 无凭据可访问（有意公开，便于外部联调）。"""
    for path in KEPT_DOC_PATHS:
        assert client.get(path).status_code == 200, path


def _load_schema(client) -> dict:
    """取 `/api/schema/`（默认 YAML 渲染）并解析为 dict。"""
    resp = client.get("/api/schema/")
    assert resp.status_code == 200
    return yaml.safe_load(resp.content.decode("utf-8"))


def test_every_operation_has_a_description(client):
    """每个 operation 都有非空说明：删除手写文档后中文可读性不丢。"""
    schema = _load_schema(client)
    missing = [
        f"{method.upper()} {path}"
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
        if method in HTTP_METHODS and not (operation.get("description") or operation.get("summary"))
    ]
    assert missing == [], f"缺少说明的端点: {missing}"


def test_every_tag_has_a_chinese_description(client):
    """每个分组（tag）都有中文说明，Swagger 分组标题可读。"""
    schema = _load_schema(client)
    tags = schema.get("tags") or []
    assert tags, "schema 未声明任何 tag 说明（SPECTACULAR_SETTINGS['TAGS'] 缺失？）"
    undocumented = [tag["name"] for tag in tags if not (tag.get("description") or "").strip()]
    assert undocumented == [], f"缺少说明的分组: {undocumented}"


def test_swagger_ui_has_no_third_party_assets(client):
    """文档页不引用任何第三方域名：断网环境也要能渲染。"""
    html = client.get("/api/swagger/").content.decode("utf-8")
    external = THIRD_PARTY_ASSET.findall(html)
    assert external == [], f"文档页仍引用外部资源: {external}"


def test_swagger_ui_assets_are_served_same_origin(client):
    """文档页引用的同源静态资产全部可取，否则页面白屏。

    说明：pytest-django 会把 `DEBUG` 置为 False，此时 URLconf 里的静态服务不注册
    （`staticfiles_urlpatterns()` 无 DEBUG 即空表），所以这里直接走与开发服务器同一个
    `staticfiles serve` 视图（finders → 文件）来验证资产可取，而不是发 HTTP 请求。
    """
    html = client.get("/api/swagger/").content.decode("utf-8")
    assets = sorted(set(SAME_ORIGIN_ASSET.findall(html)))
    assert assets, "文档页未引用任何同源静态资产（SWAGGER_UI_DIST=SIDECAR 未生效？）"

    factory = RequestFactory()
    for asset in assets:
        relative_path = asset.removeprefix("/static/")
        response = serve(factory.get(asset), relative_path, insecure=True)
        assert response.status_code == 200, f"静态资产不可取: {asset}"
