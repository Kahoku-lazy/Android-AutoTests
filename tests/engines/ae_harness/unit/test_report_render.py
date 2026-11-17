"""
文件名: ➡️ test_report_render.py 🏁
路径: ➡️ tests/engines/ae_harness/unit/test_report_render.py 🏁
模块功能：➡️ 锁住执行报告的折叠契约：三层挂点、默认收起、状态标记与轨迹行展开 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/engines/ae_harness/unit/test_report_render.py -q 🏁
时间：➡️ 2026-11-17 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-17 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 只断言渲染出来的 HTML 文本，不启浏览器：能挡住「改样式顺手删挂点」，不判断好不好看。
2. 覆盖报告区三层（子目标 / 角色块 / 工具卡）与轨迹区调用行的折叠标记。
3. 锁排版契约：品牌字体内联、字号三档（12 / 14 / 16）、侧栏默认三成且窄屏不渲染手柄。
🏁
关联模块：➡️
1. engines.ae_harness.event.render: HtmlReportRenderer，被测对象。
2. engines.ae_harness.event.record: RunRecord / StepRecord，构造最小记录。
🏁
测试：➡️
1. 本文件即测试。
🏁
"""

from __future__ import annotations

import re

from pathlib import Path

import pytest

from engines.ae_harness.event.record import RunRecord, StepRecord
from engines.ae_harness.event.render import HtmlReportRenderer

pytestmark = [pytest.mark.unit]

# 报告区 5 个标题行（1 个子目标 + 2 个角色块 + 2 张工具卡）加轨迹区 2 个调用行。
_FOLD_HEADS = 7


def _step(index: int, role: str, tool: str) -> StepRecord:
    """
    造一条步骤记录。

    Args:
        index: 步序号。
        role: agent 角色名。
        tool: 工具名。

    Returns:
        StepRecord 实例。
    """
    return StepRecord(
        index=index,
        tool=tool,
        phase="执行阶段",
        t_ms=index * 1000.0,
        state="success",
        input='{"serial": "1.2.3.4:5555"}',
        output='{"status": true}',
        note="先看一下屏幕。",
        round_index=index,
        span_ms=840.3,
        agent_role=role,
        sop_step="启动应用并进入 H6810 详情页",
    )


def _record(tmp_path: Path) -> RunRecord:
    """
    造一份最小运行记录：一个子目标、执行者与验收者各一步。

    Args:
        tmp_path: 报告落盘目录。

    Returns:
        RunRecord 实例。
    """
    return RunRecord(
        task="最小任务",
        cost_s=12.5,
        steps=[_step(1, "executor", "adb_screenshot"), _step(2, "verifier", "adb_app_state")],
        events=[],
        summary={"failed": 0, "by_tool": {"adb_screenshot": 1}, "tokens": {}},
        final_text="",
        directory=tmp_path,
        log_path=tmp_path / "run.jsonl",
        html_path=tmp_path / "run.html",
        spans=[
            {
                "kind": "model",
                "name": "deepseek-flash",
                "round": 1,
                "step": 0,
                "start_ms": 0,
                "end_ms": 10,
            },
            {
                "kind": "tool",
                "name": "adb_screenshot",
                "round": 1,
                "step": 1,
                "start_ms": 10,
                "end_ms": 20,
            },
        ],
    )


def test_three_layers_have_fold_heads(tmp_path: Path) -> None:
    """
    子目标 / 角色块 / 工具卡三层都要有可折叠标题行，且初始都是收起。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    # 子目标标题放在 h3 里（保住标题语义），按钮只包标题文字；角色块与工具卡的标题行本身就是按钮。
    assert '<button type="button" class="fold-h" aria-expanded="false"' in page
    assert '<button type="button" class="role-h fold-h" aria-expanded="false"' in page
    assert '<button type="button" class="card-h fold-h" aria-expanded="false"' in page
    assert page.count('aria-expanded="false"') == _FOLD_HEADS
    assert page.count("toggleFold(this)") == _FOLD_HEADS


def test_bodies_start_collapsed(tmp_path: Path) -> None:
    """
    三层的正文容器都要带收起类，且默认没有 is-open。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert 'class="phase fold-box"' in page
    assert 'class="role-block fold-box"' in page
    assert 'class="card fold-box"' in page
    assert 'class="phase-b fold-b"' in page
    assert 'class="role-b fold-b"' in page
    assert 'class="card-b fold-b"' in page
    assert re.search(r'class="[^"]*\bis-open\b', page) is None
    assert ".fold-box.is-open > .fold-b { display: block; }" in page


def test_collapsed_card_head_keeps_identity(tmp_path: Path) -> None:
    """
    收起后的卡片标题行仍带序号、工具名与耗时。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert '<span class="no">1</span><span class="tool">adb_screenshot</span>' in page
    assert '<span class="t ml">840.3 ms</span>' in page


def test_toggle_script_is_shared_and_syncs_aria(tmp_path: Path) -> None:
    """
    折叠只走一个状态源：切换函数同时改类、aria-expanded 与箭头。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert "function toggleFold(head)" in page
    assert 'head.closest(".fold-box")' in page
    assert 'classList.toggle("is-open")' in page
    assert 'setAttribute("aria-expanded"' in page
    # 标题行是真 <button>，靠浏览器原生把 Enter / Space 转成 click，不再自己处理按键。
    assert "foldKey" not in page
    assert "toggleTrace" not in page


def test_trace_body_collapsed_by_default(tmp_path: Path) -> None:
    """
    轨迹行详情默认收起，且不再有没人用的 .call-b 死规则。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert 'class="trace-body fold-b"' in page
    assert 'class="call fold-box"' in page
    assert ".call-b {" not in page
    assert ".call.open" not in page


def test_tips_match_behavior(tmp_path: Path) -> None:
    """
    报告页与轨迹页的提示文案必须描述真实交互。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert "点标题逐层展开" in page
    assert "点行展开该次调用的详情" in page


def test_subgoal_ordinal_is_svg_drawn(tmp_path: Path) -> None:
    """
    子目标序号必须是 SVG 描边画出来的，且每行一个、共用一份渐变与滤镜定义。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert 'class="ord-defs"' in page
    assert '<linearGradient id="ord-grad-red"' in page
    assert '<linearGradient id="ord-grad-blue"' in page
    assert '<filter id="ord-crayon"' in page
    assert page.count('class="ord"') == 1
    assert 'aria-label="第 1 个子目标"' in page
    # 两位数各画「淡墨 + 主笔画」两层，左位红、右位蓝。
    assert page.count('class="ord-ink ') == 2
    assert page.count('class="ord-soft ') == 2
    assert page.count('"ord-ink ord-red"') == 1
    assert page.count('"ord-ink ord-blue"') == 1
    assert page.count('"ord-soft ord-red"') == 1
    assert page.count('"ord-soft ord-blue"') == 1
    # 浓度口径：两支笔画都从 45% 淡到 30%。
    assert "stop-color:var(--color-red-40);stop-opacity:.45" in page
    assert "stop-color:var(--color-blue-47);stop-opacity:.45" in page
    assert "stop-color:var(--color-red-40);stop-opacity:.3" in page
    assert "stop-color:var(--color-blue-47);stop-opacity:.3" in page


def test_ordinal_caps_at_99(tmp_path: Path) -> None:
    """
    序号按 01、02 递增，超过 99 就封顶在 99。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    steps = [_step(index, "executor", "adb_screenshot") for index in range(1, 101)]
    for index, step in enumerate(steps, start=1):
        step.sop_step = f"子目标 {index}"
    record = RunRecord(
        task="一百个子目标",
        cost_s=1.0,
        steps=steps,
        events=[],
        summary={"failed": 0, "by_tool": {}, "tokens": {}},
        final_text="",
        directory=tmp_path,
        log_path=tmp_path / "run.jsonl",
        html_path=tmp_path / "run.html",
    )
    page = HtmlReportRenderer().render(record)

    assert 'aria-label="第 1 个子目标"' in page
    assert 'aria-label="第 99 个子目标"' in page
    assert 'aria-label="第 100 个子目标"' not in page
    assert page.count('class="ord"') == 100


def test_platform_brand_font_is_inlined(tmp_path: Path) -> None:
    """
    品牌字体必须内联成 data URI：报告由前端以 blob: 打开、也可能走 file://，相对路径取不到 ttf。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert 'src: url("data:font/ttf;base64,' in page
    # 老写法是 ../../../../frontend/public/fonts/ziku-feiyang.ttf：blob: 里解析不了，
    # 字体静默 404 后标题回落系统黑体——正是「两处标题栏和平台字体不一样」的成因。
    assert "frontend/public/fonts" not in page
    assert ".ttf\") format" not in page


def test_type_scale_is_three_tiers(tmp_path: Path) -> None:
    """
    字号只三档：时间与日期 12、正文 14、标题与小标题 16；页面标题栏维持平台档位。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    # 正文 14：任务正文、验收事项、提示语、侧栏列表与 token 行、结果 JSON、事件字段。
    assert ".task .v { font-size: var(--app-size-sm)" in page
    assert ".check-card li { font-size: var(--app-size-sm)" in page
    assert ".tip { font-size: var(--app-size-sm)" in page
    assert ".task-box p { margin: 0; font-size: var(--app-size-sm)" in page
    assert ".side-list { list-style: none; margin: 0 0 16px; padding: 0; font-size: var(--app-size-sm); }" in page
    assert "align-items: baseline; font-size: var(--app-size-sm); padding: 3px 0;" in page
    assert "font-size: var(--app-size-sm); align-items: start;" in page
    assert "font-size: var(--app-size-sm); white-space: pre-wrap; word-break: break-all;" in page
    assert "white-space: pre-wrap; word-break: break-all; font-size: var(--app-size-sm); }" in page

    # 时间与日期 12：耗时、调用次数、事件时间列、标签与 Badge。
    assert ".t { font-family: var(--app-font-mono); font-size: var(--app-size-xs)" in page
    assert ".log-t { font-size: var(--app-size-xs)" in page
    assert ".phase-h em { font-style: normal; font-size: var(--app-size-xs)" in page

    # 标题与小标题 16：子目标标题、工具卡标题、图表卡标题、表头。
    assert ".phase-h h3 { flex: 1 1 auto; min-width: 0; font-size: var(--app-size-md)" in page
    assert ".tool { font-family: var(--app-font-mono); font-size: var(--app-size-md)" in page
    assert "margin: 0 0 10px; font-size: var(--app-size-md); font-weight: 800;" in page
    assert "table.marks th { background: var(--app-bg-subtle); font-size: var(--app-size-md)" in page

    # 两处页面标题栏不压到 16：侧栏品牌 20、页头 24（与平台 WorkbenchHeader 同档）。
    assert "font-size: var(--app-size-lg);\n  font-weight: 400;\n  letter-spacing: 0;" in page
    assert "font-size: var(--app-size-xl); font-weight: 400; margin: 0; letter-spacing: 0;" in page


def test_sidebar_defaults_to_thirty_percent_and_is_draggable(tmp_path: Path) -> None:
    """
    侧栏默认占三成宽，带可拖可键盘的分栏手柄；两栏退化成单栏时不渲染手柄。

    Args:
        tmp_path: pytest 临时目录。

    Returns:
        无。
    """
    page = HtmlReportRenderer().render(_record(tmp_path))

    assert "--side-w:30%; --side-min:220px; --side-max:760px;" in page
    assert 'id="splitter"' in page
    assert 'role="separator"' in page
    assert 'aria-orientation="vertical"' in page
    assert "cursor: col-resize" in page
    assert "function initSplitter()" in page
    assert "initSplitter();" in page
    # 快捷键与边界照平台 shared/components/SplitHandle.vue：16 / Shift 48、Home / End、双击回默认。
    assert "const step = event.shiftKey ? 48 : 16;" in page
    assert 'event.key === "Home"' in page
    assert 'event.key === "End"' in page
    assert "DEFAULT_RATIO = .3" in page
    assert "const RIGHT_MIN = 480;" in page
    # 两栏退化成单栏后没有可拖的分界。
    assert ".splitter { display: none; }" in page
