"""灰盒·单元测试 — 动作日志证据窗口（device-log-evidence 能力）。

零外部依赖、不连设备、不占用固定端口。
覆盖：开窗语义、四等级标注（用 17:01:12.645 那组参考时间精确复现）、周期性识别、
多条命中全量返回、未命中 / 无日志降级、未开窗报错、关键词表数据驱动。
"""

from __future__ import annotations

import time

from pathlib import Path

import pytest

from engines.device.logbus import (
    CONCLUSION_HIT,
    CONCLUSION_NO_HIT,
    CONCLUSION_NO_LOG,
    CONCLUSION_OUT_OF_WINDOW,
    GRADE_BEFORE,
    GRADE_OUT,
    GRADE_PERIODIC,
    GRADE_STRONG,
    KeywordIndex,
    LogBus,
    LogBusConfig,
    LogLine,
    LogWindowMissing,
    build_evidence,
    now_stamp,
    parse_stamp,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
KEYWORD_FILE = REPO_ROOT / "config" / "device_log_keywords.json"

ACTION_TIME = "2026-09-28 17:01:12.645"
WINDOW_OPENED = "2026-09-28 17:01:10.000"

KEYWORDS = KeywordIndex(
    {
        "switch_on": [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}],
        "switch_off": [{"id": 1, "module": "设备开关", "feature": "关闭设备成功"}],
        "lumi_set_success": [{"id": 6, "module": "亮度", "feature": "成功设置相对亮度"}],
        "color_configs_set_success": [
            {"id": 2, "module": "灯效库", "feature": "设置颜色成功"},
            {"id": 17, "module": "颜色模式", "feature": "分段-颜色设置成功"},
        ],
    }
)


def _line(stamp: str, text: str, source: str = "tcp") -> LogLine:
    moment = parse_stamp(stamp)
    assert moment is not None
    return LogLine(
        channel="*",
        timestamp=stamp,
        epoch=moment.timestamp(),
        source=source,
        text=text,
    )


def _evidence(lines: list[LogLine], action_time: str = ACTION_TIME) -> dict:
    return build_evidence(
        channel="*",
        window_id="w1",
        window_opened_at=WINDOW_OPENED,
        lines=lines,
        keywords=KEYWORDS,
        action_time=action_time,
        threshold_seconds=5.0,
        baseline_seconds=30.0,
    )


# ── 3.2 参考时间线：四等级 ───────────────────────────────────


def test_reference_timeline_grades_only_within_five_seconds() -> None:
    """复现需求方给的参考时间线：动作前的行标「动作前」，+60s / +120s 标「超窗」且不作证据。"""
    lines = [
        _line("2026-09-28 17:01:11.645", "[APP] switch_on"),
        _line("2026-09-28 17:02:12.645", "[APP] switch_on"),
        _line("2026-09-28 17:03:12.645", "[APP] switch_on"),
    ]
    evidence = _evidence(lines)

    assert evidence["action_time"] == ACTION_TIME
    assert evidence["hits"] == []
    assert evidence["conclusion"] == CONCLUSION_OUT_OF_WINDOW
    assert [item["timestamp"] for item in evidence["before_action"]] == ["2026-09-28 17:01:11.645"]
    assert evidence["before_action"][0]["grade"] == GRADE_BEFORE
    assert [item["delta_seconds"] for item in evidence["out_of_window"]] == [60.0, 120.0]
    assert {item["grade"] for item in evidence["out_of_window"]} == {GRADE_OUT}


def test_hit_within_threshold_is_strong_evidence() -> None:
    """窗口内首次出现（动作前基线无同名日志）→ 强证据。"""
    lines = [_line("2026-09-28 17:01:13.104", "[APP] switch_on")]
    evidence = _evidence(lines)

    assert evidence["conclusion"] == CONCLUSION_HIT
    assert len(evidence["hits"]) == 1
    hit = evidence["hits"][0]
    assert hit["keyword"] == "switch_on"
    assert hit["grade"] == GRADE_STRONG
    assert hit["count"] == 1
    assert hit["features"] == [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}]
    assert hit["baseline_occurrences"] == []


# ── 3.3 周期性识别（不剔除）─────────────────────────────────


def test_periodic_log_is_flagged_and_kept() -> None:
    """动作前基线窗口内已出现同名日志 → 标「疑似周期」，仍留在证据里并附动作前行。"""
    lines = [
        _line("2026-09-28 17:01:11.645", "[APP] switch_on"),
        _line("2026-09-28 17:01:13.104", "[APP] switch_on"),
    ]
    evidence = _evidence(lines)

    assert evidence["conclusion"] == CONCLUSION_HIT
    hit = evidence["hits"][0]
    assert hit["grade"] == GRADE_PERIODIC
    assert hit["count"] == 1
    assert [item["timestamp"] for item in hit["baseline_occurrences"]] == [
        "2026-09-28 17:01:11.645"
    ]
    # 动作前的那条同时以「动作前」等级出现在上下文里
    assert evidence["before_action"][0]["grade"] == GRADE_BEFORE


def test_baseline_outside_window_is_not_periodic() -> None:
    """动作前基线窗口之外的同名日志不构成「疑似周期」。"""
    lines = [
        _line("2026-09-28 17:00:10.000", "[APP] switch_on"),  # 动作前 62 秒 > 30 秒基线
        _line("2026-09-28 17:01:13.104", "[APP] switch_on"),
    ]
    evidence = _evidence(lines)
    assert evidence["hits"][0]["grade"] == GRADE_STRONG


# ── 3.4 多条命中全量返回 ─────────────────────────────────────


def test_multiple_keywords_are_all_returned() -> None:
    """一次动作触发多个关键词 → 全部返回。"""
    lines = [_line("2026-09-28 17:01:13.104", "[APP] switch_on then switch_off")]
    evidence = _evidence(lines)
    assert {hit["keyword"] for hit in evidence["hits"]} == {"switch_on", "switch_off"}


def test_repeated_keyword_reports_count_and_all_timestamps() -> None:
    """同一关键词在窗口内出现多次 → 返回次数与各次时间戳。"""
    lines = [
        _line("2026-09-28 17:01:13.104", "[APP] switch_on"),
        _line("2026-09-28 17:01:13.704", "[APP] switch_on"),
        _line("2026-09-28 17:01:14.204", "[APP] switch_on"),
    ]
    evidence = _evidence(lines)
    hit = evidence["hits"][0]
    assert hit["count"] == 3
    assert hit["timestamps"] == [
        "2026-09-28 17:01:13.104",
        "2026-09-28 17:01:13.704",
        "2026-09-28 17:01:14.204",
    ]


def test_shared_keyword_returns_all_features() -> None:
    """共用关键词命中时返回全部功能点（歧义交模型判断）。"""
    lines = [_line("2026-09-28 17:01:13.104", "[APP] color_configs_set_success")]
    evidence = _evidence(lines)
    assert {item["id"] for item in evidence["hits"][0]["features"]} == {2, 17}


# ── 一步多次动作：取证窗取并集（真机验证暴露的口径）─────────

MULTI_ACTIONS = [
    "2026-09-28 12:46:49.177",
    "2026-09-28 12:46:54.626",
    "2026-09-28 12:46:58.830",
    "2026-09-28 12:47:02.872",
]


def _multi_action_evidence(action_times: list[str], lines: list[LogLine]) -> dict:
    return build_evidence(
        channel="H6810",
        window_id="w9",
        window_opened_at="2026-09-28 12:46:45.000",
        lines=lines,
        keywords=KEYWORDS,
        action_times=action_times,
        threshold_seconds=5.0,
        baseline_seconds=30.0,
    )


def test_multi_action_step_counts_response_to_any_action() -> None:
    """真机 case：一步 4 次点击，灯在最后一次点击后 0.6 秒响应 → 算本次证据。"""
    lines = [_line("2026-09-28 12:47:03.486", "[brightness][I]: lumi_set_success")]
    evidence = _multi_action_evidence(MULTI_ACTIONS, lines)
    assert evidence["conclusion"] == CONCLUSION_HIT
    hit = evidence["hits"][0]
    assert hit["keyword"] == "lumi_set_success"
    assert hit["grade"] == GRADE_STRONG
    assert evidence["action_times"] == MULTI_ACTIONS


def test_only_first_action_would_misjudge_as_out_of_window() -> None:
    """只认首次动作的旧口径会把这次真实响应判成超窗（缺陷回归）。"""
    lines = [_line("2026-09-28 12:47:03.486", "[brightness][I]: lumi_set_success")]
    evidence = _multi_action_evidence(MULTI_ACTIONS[:1], lines)
    assert evidence["conclusion"] == CONCLUSION_OUT_OF_WINDOW
    assert evidence["hits"] == []
    assert evidence["out_of_window"][0]["delta_seconds"] == pytest.approx(14.309, abs=0.001)


def test_step_gap_line_stays_in_raw_log_without_grade() -> None:
    """本步内但不在任何一次动作 5 秒窗内的行：不进等级列表，仍留在原始日志。"""
    actions = ["2026-09-28 12:46:49.177", "2026-09-28 12:47:09.177"]  # 两次动作相隔 20 秒
    lines = [
        _line("2026-09-28 12:46:58.000", "[noise] lumi_set_success"),  # 落在两次动作中间的空隙
        _line("2026-09-28 12:47:09.800", "[brightness][I]: lumi_set_success"),  # 第二次动作后 0.6s
    ]
    evidence = _multi_action_evidence(actions, lines)
    assert [hit["count"] for hit in evidence["hits"]] == [1]
    assert evidence["before_action"] == []
    assert evidence["out_of_window"] == []
    assert len(evidence["lines"]) == 2  # 空隙行仍在原始日志里


# ── 3.5 未命中 / 无日志降级 ──────────────────────────────────


def test_lines_without_hit_still_return_raw_log() -> None:
    """窗口内有日志但没命中 → 仍返回原始日志，结论为 no_hit。"""
    lines = [_line("2026-09-28 17:01:13.104", "ram free heap size: 11636")]
    evidence = _evidence(lines)
    assert evidence["conclusion"] == CONCLUSION_NO_HIT
    assert evidence["hits"] == []
    assert [item["text"] for item in evidence["lines"]] == ["ram free heap size: 11636"]


def test_empty_window_reports_no_log() -> None:
    """窗口内一条日志都没有 → 结论为 no_log。"""
    evidence = _evidence([])
    assert evidence["conclusion"] == CONCLUSION_NO_LOG
    assert evidence["lines"] == []
    assert evidence["window_line_count"] == 0


# ── 3.1 / 3.6 窗口语义 ───────────────────────────────────────


def test_window_excludes_lines_before_open() -> None:
    """开窗前的行不进窗口，开窗后的行进窗口。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus.feed("before-open")
    time.sleep(0.05)  # 让时钟走一格，确保「开窗前的行」严格早于窗口起点
    window_id = bus.open_window(device="dev-1", label="step 1")
    bus.feed("[APP] switch_on")

    evidence = bus.read_window(device="dev-1", window_id=window_id, action_time=now_stamp())
    assert [item["text"] for item in evidence["lines"]] == ["[APP] switch_on"]
    assert bus.snapshot(channel="*")[0]["text"] == "before-open"  # 历史仍在缓冲里，只是不进窗口


def test_window_is_isolated_per_device_channel() -> None:
    """按设备隔离：另一台设备的日志不进本设备的窗口。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus.register_device_channel("dev-a", "chan-a")
    bus.register_device_channel("dev-b", "chan-b")

    window_id = bus.open_window(device="dev-a", label="step 1")
    action_time = now_stamp()  # 基准取在灌日志之前
    bus.feed("a-line", channel="chan-a")
    bus.feed("b-line", channel="chan-b")

    evidence = bus.read_window(device="dev-a", window_id=window_id, action_time=action_time)
    assert [item["text"] for item in evidence["lines"]] == ["a-line"]


def test_read_without_open_window_raises() -> None:
    """未开窗就读窗 → 报可读错误，不用历史日志顶替。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus.feed("[APP] switch_on")
    with pytest.raises(LogWindowMissing):
        bus.read_window(device="dev-1")


# ── 关键词表数据驱动 ─────────────────────────────────────────


def test_keyword_file_is_data_driven() -> None:
    """关键词表从数据文件加载：67 个关键词 / 56 个功能点，共用关键词返回多个功能点。"""
    index = KeywordIndex.from_file(KEYWORD_FILE)
    assert len(index) == 67
    feature_ids = {item["id"] for values in index.mapping.values() for item in values}
    assert feature_ids == set(range(56))
    hits = index.match("[APP] color_configs_set_success done")
    assert hits[0][0] == "color_configs_set_success"
    assert {item["id"] for item in hits[0][1]} == {2, 17}


def test_longer_keyword_wins_over_contained_one() -> None:
    """长关键词优先：viewing_..._open 不会被误判成 video_sound_effect_open。"""
    index = KeywordIndex.from_file(KEYWORD_FILE)
    hits = index.match("viewing_dreamview_video_sound_effect_open")
    assert [name for name, _ in hits] == ["viewing_dreamview_video_sound_effect_open"]
