"""灰盒·单元测试 — 设备日志历史取证（变更 debug-verifier-log-evidence）。

零外部依赖：用临时日志文件与临时关键词表断言五条口径 ——
1. 基准时刻识别取文本里**第一个**北京时间毫秒时间戳，识别不到返回空串；
2. 按基准 + 阈值从文件切窗，命中关键词并给出等级与时间戳（与任务链路同一份判定）；
3. 基准早于所读文件范围时如实给「窗口内无日志」，不抛错；
4. 文件缺失 / 目录未配置 / 没有端口来源时如实给出原因，不抛错；
5. 没给基准时退回「最近一个取证窗」，`from_message` 为假。
"""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from apps.ai_assistant import log_history

KEYWORD = "switch_on"
BASIS = "2026-09-29 11:47:04.326"
LOG_LINES = [
    "2026-09-29 11:46:00.000 [tcp] ram free heap size: 11400",
    "2026-09-29 11:47:04.687 [tcp] [light_switch][I]: switch_on",
    "2026-09-29 11:47:04.742 [tcp] [base mode][I]: music_mode_start",
    "2026-09-29 11:47:20.000 [tcp] ram free heap size: 11368",
]


@pytest.fixture()
def log_env(tmp_path: Path, settings):
    """临时日志目录 + 关键词表 + 单个端口来源（H6810/7005）。"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "H6810_7005.log").write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
    keyword_file = tmp_path / "keywords.json"
    keyword_file.write_text(
        json.dumps(
            {"keywords": {KEYWORD: [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}]}},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    settings.DEVICE_LOG_LOG_DIR = str(log_dir)
    settings.DEVICE_LOG_KEYWORD_FILE = str(keyword_file)
    settings.DEVICE_LOG_SOURCES = json.dumps({"7005": {"sku": "H6810"}})
    settings.DEVICE_LOG_WINDOW_SECONDS = 5.0
    settings.DEVICE_LOG_BASELINE_SECONDS = 30.0
    return log_dir


def history(basis: str, **kwargs) -> dict:
    """单测入口：显式声明采集可用（真实开关走 DB，此处不碰库）。"""
    return log_history.history_evidence(basis, capture_enabled=True, **kwargs)


def test_extract_basis_time_takes_first() -> None:
    text = f"执行模型返回：{BASIS}\n后来又提到 2026-09-29 11:47:20.000"
    assert log_history.extract_basis_time(text) == BASIS
    assert log_history.extract_basis_time("没有任何时刻的文本") == ""
    assert log_history.extract_basis_time("") == ""


def test_history_evidence_hits_keyword(log_env) -> None:
    result = history(BASIS)
    evidence = result["evidence"]
    assert result["from_message"] is True
    assert result["basis_time"] == BASIS
    assert result["note"] == ""
    assert evidence is not None
    assert evidence["conclusion"] == "hit"
    assert [hit["keyword"] for hit in evidence["hits"]] == [KEYWORD]
    # 命中出现在取证窗内（点击 +0.361s），且带功能点与等级
    hit = evidence["hits"][0]
    assert hit["timestamps"] == ["2026-09-29 11:47:04.687"]
    assert hit["grade"] == "strong"
    assert hit["features"][0]["feature"] == "打开设备成功"
    # 动作前基线里的行不计命中；窗口内原始日志含行
    assert evidence["window_line_count"] >= 2
    assert result["files"][0].endswith("H6810_7005.log")


def test_history_evidence_out_of_read_range_is_empty(log_env) -> None:
    """基准早于文件里最早的行时：如实给「窗口内无日志」，不抛错。"""
    result = history("2026-09-29 09:00:00.000")
    assert result["note"] == log_history.NOTE_NO_LOG
    assert result["evidence"] is not None
    assert result["evidence"]["conclusion"] == "no_log"
    assert result["evidence"]["hits"] == []


def test_history_evidence_missing_file(tmp_path: Path, settings, log_env) -> None:
    (log_env / "H6810_7005.log").unlink()
    result = history(BASIS)
    assert result["note"] == log_history.NOTE_NO_FILE
    assert result["files"] == []


def test_history_evidence_without_source(settings, log_env) -> None:
    settings.DEVICE_LOG_SOURCES = "{}"
    settings.DEVICE_LOG_TCP_PORT = 0
    result = history(BASIS)
    assert result["evidence"] is None
    assert result["note"] == log_history.NOTE_NO_SOURCE


def test_history_evidence_respects_listen_switch(log_env) -> None:
    """监听开关关着（调用方判定不可用）：不读文件、不取证据、也不替用户打开端口。"""
    result = log_history.history_evidence(BASIS, capture_enabled=False)
    assert result["evidence"] is None
    assert result["files"] == []
    assert result["note"] == log_history.NOTE_NO_LISTEN


def test_history_evidence_falls_back_to_recent_window(log_env) -> None:
    """没给基准时退回「最近一个取证窗」，并标明基准不是来自消息。"""
    result = history("")
    assert result["from_message"] is False
    assert result["basis_time"]
    assert result["evidence"] is not None
    # 最近窗（今天 11:47 之后的日志不在「现在」附近）→ 结论如实为空或未命中，但必须有结论
    assert result["evidence"]["conclusion"] in {"no_log", "no_hit", "out_of_window"}
