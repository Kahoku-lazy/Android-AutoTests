"""YAML 用例加载、占位符解析与执行断言。

用例字段约定（见 tests/api/case/*.yaml）：
  - id / title / point  编号 / 测试标题 / 测试点
  - method / path       请求方法与路径
  - body / raw_body     请求体（json / 原始文本）
  - expect.status       期望 HTTP 状态码
  - expect.schema       响应 JSONSchema 名（见 schemas.SCHEMAS）
  - expect.check        定点字段断言（点分路径 -> 期望值，支持占位符）
"""

from pathlib import Path
from typing import Any

import jsonschema
import yaml

from tests.api.schemas import SCHEMAS

CASE_DIR = Path(__file__).resolve().parent / "case"


def load_cases(filename: str) -> list[dict]:
    """加载 tests/api/case/{filename}，返回用例列表。"""
    path = CASE_DIR / filename
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def resolve(value: Any, **ctx: str) -> Any:
    """递归替换字符串中的 {{key}} 占位符。"""
    if isinstance(value, str):
        for key, val in ctx.items():
            value = value.replace("{{" + key + "}}", str(val))
        return value
    if isinstance(value, dict):
        return {k: resolve(v, **ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, **ctx) for v in value]
    return value


def get_path(obj: Any, dotted: str) -> Any:
    """按点分路径取值，如 data.user.username。"""
    for part in dotted.split("."):
        obj = obj[part]
    return obj


def execute_case(base_url: str, api_session, case: dict, ctx: dict) -> None:
    """按 YAML 用例执行并断言：状态码 + JSONSchema + 定点字段。"""
    method = case.get("method", "POST")
    url = f"{base_url}{case['path']}"
    if "raw_body" in case:
        resp = api_session.request(method, url, data=case["raw_body"])
    else:
        body = resolve(case.get("body", {}), **ctx)
        resp = api_session.request(method, url, json=body)

    data = resp.json()
    expect = case["expect"]

    assert resp.status_code == expect["status"], (
        f"{case['id']}（{case['title']}）: 期望 {expect['status']}，实际 {resp.status_code}: {data}"
    )
    jsonschema.validate(instance=data, schema=SCHEMAS[expect["schema"]])

    for path, expected in (expect.get("check") or {}).items():
        expected = resolve(expected, **ctx)
        actual = get_path(data, path)
        assert actual == expected, (
            f"{case['id']}（{case['title']}）: {path} 期望 {expected!r}，实际 {actual!r}"
        )
