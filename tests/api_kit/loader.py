from pathlib import Path
from typing import Any

import jsonschema
import yaml

from tests.api_kit.schemas import SCHEMAS

CASE_DIR = Path(__file__).resolve().parents[1] / "api" / "case"


def load_cases(filename: str) -> list[dict]:
    path = CASE_DIR / filename
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def resolve(value: Any, **ctx: str) -> Any:
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
    for part in dotted.split("."):
        obj = obj[part]
    return obj


def execute_case(base_url: str, api_session, case: dict, ctx: dict) -> None:
    method = case.get("method", "POST")
    url = f"{base_url}{case['path']}"
    if "raw_body" in case:
        resp = api_session.request(method, url, data=case["raw_body"])
    elif method.upper() == "GET":
        resp = api_session.request(method, url)
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
