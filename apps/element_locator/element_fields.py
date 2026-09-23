"""元素字段校验与规整 —— 新增 / 更新共用的唯一校验口径。

校验放在 api 层执行：前端校验只是体验，后端校验才是防线。
本模块只被 element_locator 内部的 api / views 使用，不对外暴露。

口径（rework-save-to-elements）：呈现与写入收敛为「缩略图 / 元素名称 / 序号 / 文本 / 主定位 /
交互标注 / 测试点」。更新只接受呈现列里可编辑的四项；新增额外接受备注与去重键
（resource_id 与 bounds 至少一个）。类名、内容描述、坐标分量、层级、父内序号与候选 XPath
列表不再由工作台写入。
"""

from __future__ import annotations

import re

from typing import Any

# 与 models.Element 的列宽对齐（长度校验的唯一真相源）
STRING_MAX_LENGTH = {
    "alias": 500,
    "text_val": 2000,
    "primary_xpath": 2000,
    "resource_id": 500,
}

BOOL_FIELDS = ("is_test_point",)

# 呈现列里可编辑的四项（行内更新）
UPDATE_FIELDS = ("alias", "text_val", "primary_xpath", "is_test_point")

# 新增额外接受备注与去重键（resource_id 与 bounds 至少一个，用于满足唯一约束）
CREATE_FIELDS = (*UPDATE_FIELDS, "notes", "resource_id", "bounds")

# [x1,y1][x2,y2]，四段均为整数
_BOUNDS_RE = re.compile(r"^\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]$")


def parse_bounds(bounds: str) -> tuple[int, int, int, int]:
    """把 [x1,y1][x2,y2] 解析为 (x, y, width, height)；非法时抛 ValueError。"""
    match = _BOUNDS_RE.match((bounds or "").strip())
    if match is None:
        raise ValueError("坐标格式应为 [x1,y1][x2,y2]")
    x1, y1, x2, y2 = (int(group) for group in match.groups())
    if x2 < x1 or y2 < y1:
        raise ValueError("坐标右下角不能小于左上角")
    return x1, y1, x2 - x1, y2 - y1


def normalize_element_fields(raw: dict[str, Any], allowed: tuple[str, ...]) -> dict[str, Any]:
    """按白名单校验并规整元素字段，返回可直接落库的 dict。非法时抛 ValueError。

    Args:
        raw: 入参字段（snake_case）。
        allowed: 本次写入允许的字段集合（更新 `UPDATE_FIELDS` / 新增 `CREATE_FIELDS`）。
    """
    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        if key not in allowed:
            raise ValueError(f"不支持修改字段 {key}")

        if key in BOOL_FIELDS:
            normalized[key] = bool(value)
            continue

        if key == "bounds":
            normalized["bounds"] = ("" if value is None else str(value)).strip()
            x, y, width, height = (
                parse_bounds(normalized["bounds"]) if normalized["bounds"] else (0, 0, 0, 0)
            )
            normalized.update({"x": x, "y": y, "width": width, "height": height})
            continue

        text = "" if value is None else str(value)
        limit = STRING_MAX_LENGTH.get(key)
        if limit is not None and len(text) > limit:
            raise ValueError(f"{key} 最长 {limit} 个字符")
        normalized[key] = text

    # 人工写入的主定位是单条表达式，无法判定「同页唯一匹配」→ 一律标记为不稳定
    if "primary_xpath" in normalized:
        if not normalized["primary_xpath"].strip():
            raise ValueError("主定位表达式不能为空")
        normalized["primary_stable"] = False

    return normalized
