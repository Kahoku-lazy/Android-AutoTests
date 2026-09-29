"""灰盒·单元测试 — 参数标签的前后端契约对拍（变更 localize-tool-debug-params）。

只读源码、只做一致性断言（与 `test_auth_frontend_contract.py` 同一范式）：
1. 调试页模板使用中文标签函数，并保留英文参数名与必填/可选标注；
2. 说明以悬浮提示（title）呈现，不在正文铺开；
3. 参数 DTO 声明了 label / hint；
4. 前端不硬编码任何参数中文名（中文名唯一来源是后端 schema）。
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULE = REPO_ROOT / "frontend" / "src" / "modules" / "ai-assistant"
PAGE = MODULE / "ToolDebugPage.vue"
HELPER = MODULE / "helpers" / "tool-debug-label.ts"
DTO = MODULE / "api" / "toolbox.ts"

# 前端里有中文的合法位置：标签函数只允许「（ ）」分隔符与回退说明；不得出现具体参数中文名
FORBIDDEN_LABELS = ("设备序列号", "日志关键词搜索", "日志端口", "查询跨度", "应用包名")


def test_debug_page_uses_label_helper_and_keeps_english_name() -> None:
    source = PAGE.read_text(encoding="utf-8")
    assert "paramLabel(p)" in source, "参数标签必须走 paramLabel（中文名 + 英文名）"
    assert "p.required" in source and "必填" in source
    assert "可选" in source
    assert "p.type" in source, "参数类型仍需展示"


def test_debug_page_renders_hint_as_tooltip() -> None:
    source = PAGE.read_text(encoding="utf-8")
    assert ':title="p.hint' in source, "参数说明必须以悬浮提示呈现"
    assert "p.hint }}</" not in source, "说明不得直接铺在表单正文里"


def test_helper_composes_chinese_and_english() -> None:
    source = HELPER.read_text(encoding="utf-8")
    assert "param.label" in source and "param.name" in source
    assert "${label}（${param.name}）" in source, "标签拼接口径必须是「中文名（english）」"
    assert "label === param.name" in source, "回退时不得输出重复的中英同名"


def test_param_dto_declares_label_and_hint() -> None:
    source = DTO.read_text(encoding="utf-8")
    assert "label: string" in source
    assert "hint: string" in source


def test_frontend_does_not_hardcode_param_labels() -> None:
    """中文名只来自后端 schema：调试页与标签函数里不得出现具体参数中文名。"""
    for path in (PAGE, HELPER):
        source = path.read_text(encoding="utf-8")
        for label in FORBIDDEN_LABELS:
            assert label not in source, f"{path.name} 不应硬编码参数中文名 {label}"
