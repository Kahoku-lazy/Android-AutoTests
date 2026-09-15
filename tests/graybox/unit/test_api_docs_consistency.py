"""手写 API 文档（`/api/docs`）与真实路由的一致性契约。

背景：`config/api_docs.py` 是**人工维护的公开文档快照**，真相源是各 App `urls.py`。
本用例看守两件事：

1. **文档 → 代码**（严格）：文档记录的每条路径都必须能被 Django 路由解析（用 `resolve()` 探测，
   占位符按转换器尝试 `1` / `dummy` 并容错尾斜杠 —— 比字符串比对可靠，避免 DRF router 正则误报）；
2. **不许整体缩水**：模块数与端点数有下限，每个模块分组非空，且 WS 生产点为 0 时不得收录 WS 端点。

说明：本文件只收录主要业务端点（非全量：DRF `DefaultRouter` 展开、`admin/`、`static/`、`media/` 不在收录范围），
故**不做**「路由表 → 文档」的全量断言。
"""

from __future__ import annotations

import itertools
import re

import pytest

from django.test import Client
from django.urls import Resolver404, resolve

from config.api_docs import ENDPOINTS

# unit：纯逻辑；arch：跨模块不变量（文档 ↔ 路由）
pytestmark = [pytest.mark.unit, pytest.mark.arch]

# 下限（当前模块 5 / 端点 29）：低于此值说明文档被整体删薄
MIN_MODULES = 5
MIN_DOCUMENTED_ENDPOINTS = 25

PLACEHOLDER_DUMMIES = ("1", "dummy")


def _documented_rest_paths() -> list[str]:
    return [i["path"] for m in ENDPOINTS for i in m["items"] if i["method"] != "WS"]


def _probe_urls(path: str) -> list[str]:
    """把 `{x}` 占位符按若干候选值展开（兼容 `<int:id>` 与 `<str:id>` 转换器）。"""
    parts = re.split(r"(\{[^}]+\})", path)
    slots = [i for i, p in enumerate(parts) if p.startswith("{")]
    urls: list[str] = []
    for combo in itertools.product(PLACEHOLDER_DUMMIES, repeat=len(slots)):
        filled = list(parts)
        for idx, value in zip(slots, combo):
            filled[idx] = value
        base = "".join(filled)
        urls.extend([base, base.rstrip("/") + "/"])
    return urls


def _resolves(path: str) -> bool:
    """该文档路径是否真的存在于路由表。"""
    for candidate in _probe_urls(path):
        try:
            resolve(candidate)
            return True
        except Resolver404:
            continue
    return False


def test_documented_paths_exist_in_router():
    """文档 → 代码（严格）：每条已文档化的路径都必须能解析。"""
    missing = [p for p in _documented_rest_paths() if not _resolves(p)]
    assert missing == [], f"文档记录了不存在的端点: {missing}"


def test_documentation_has_not_shrunk():
    """不许整体缩水：模块数、端点数有下限，且每个分组非空。"""
    documented = _documented_rest_paths()
    assert len(ENDPOINTS) >= MIN_MODULES, f"模块数 {len(ENDPOINTS)} < {MIN_MODULES}"
    assert len(documented) >= MIN_DOCUMENTED_ENDPOINTS, (
        f"已文档化端点数 {len(documented)} < {MIN_DOCUMENTED_ENDPOINTS}"
    )
    empty = [m["module"] for m in ENDPOINTS if not m["items"]]
    assert empty == [], f"空模块分组: {empty}"


def test_no_websocket_entries_while_zero_production_points():
    """WS 生产点为 0（`gateway/routing.py` 空表）时，文档不得再收录 WS 端点。"""
    ws_items = [i["path"] for m in ENDPOINTS for i in m["items"] if i["method"] == "WS"]
    assert ws_items == [], f"文档仍收录 WS 端点: {ws_items}"


@pytest.mark.django_db
def test_api_docs_views_are_reachable():
    """/api/docs 与 /api/docs.html 两个公开文档端点仍可渲染。"""
    client = Client()
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/docs.html").status_code == 200
