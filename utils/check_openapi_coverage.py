"""
模块功能：➡️ OpenAPI 覆盖门禁：URLconf 的每条业务路径都必须出现在基线里 🏁
Python 调试：➡️ python -m utils.check_openapi_coverage 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无
🏁
"""

from __future__ import annotations

import os
import re
import sys

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "openspec" / "openapi.yaml"

# 非业务路径：DRF Router 根与文档端点，不要求出现在 schema 的业务清单里
EXCLUDED = {
    "/api/ai/",
    "/api/cases/",
    "/api/schema/",
    "/api/swagger/",
}


def _walk(patterns, prefix: str = ""):
    """递归展开 include()，逐个产出最终 URL pattern 字符串。"""
    for pattern in patterns:
        full = prefix + str(pattern.pattern)
        if hasattr(pattern, "url_patterns"):
            yield from _walk(pattern.url_patterns, full)
        else:
            yield full


def _normalize(raw: str) -> str:
    """归一化为 `/api/.../{}/.../`：去锚点、参数名统一成 `{}`。"""
    text = raw.replace("^", "").replace("$", "")
    text = re.sub(r"\(\?P<[^>]+>[^)]*\)", "{}", text)
    text = re.sub(r"<[^>]+>", "{}", text)
    text = re.sub(r"\{[^}]+\}", "{}", text)
    if not text.startswith("/"):
        text = "/" + text
    if not text.endswith("/"):
        text += "/"
    return text


def business_paths() -> set[str]:
    """URLconf 中的业务路径集合（去掉 format 变体与排除项）。"""
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
    import django

    django.setup()
    from django.urls import get_resolver

    found: set[str] = set()
    for raw in _walk(get_resolver().url_patterns):
        if not raw.startswith("api/") or "format" in raw:
            continue
        path = _normalize(raw)
        if path in EXCLUDED:
            continue
        found.add(path)
    return found


def documented_paths() -> set[str]:
    """OpenAPI 基线中的路径集合（参数名归一化）。"""
    data = yaml.safe_load(BASELINE.read_text(encoding="utf-8"))
    return {_normalize(path) for path in (data.get("paths") or {})}


def main() -> int:
    if not BASELINE.exists():
        print(f"缺少基线：{BASELINE.relative_to(ROOT)}", file=sys.stderr)
        print(
            "生成：python -m manage spectacular --file openspec/openapi.yaml --validate",
            file=sys.stderr,
        )
        return 1

    documented = documented_paths()
    missing = sorted(business_paths() - documented)
    if missing:
        print(f"OpenAPI 覆盖缺失（{len(missing)} 条）：", file=sys.stderr)
        for path in missing:
            print(f"  - {path}", file=sys.stderr)
        print(
            "更新基线：python -m manage spectacular --file openspec/openapi.yaml --validate",
            file=sys.stderr,
        )
        return 1

    print(f"OpenAPI 覆盖通过：业务路径 {len(business_paths())} 条全部已文档化")
    return 0


if __name__ == "__main__":
    sys.exit(main())
