"""角色过程日志：按天切分、追加写、固定列格式、单行化与并发安全。"""

from __future__ import annotations

import logging
import threading

import pytest

from engines.ai import process_log as process_log_module
from engines.ai.process_log import (
    SCOPE_STANDALONE,
    AgentProcessLog,
    daily_log_file,
    resolve_log_path,
)


def _fix_day(monkeypatch, stamp: str) -> None:
    """把“当天日期”固定成给定值（跨天切换用）。"""
    monkeypatch.setattr(process_log_module, "_today_stamp", lambda: stamp)


@pytest.mark.unit
def test_explicit_path_wins_and_file_is_lazy(tmp_path, monkeypatch):
    """显式基路径优先；未写入前不创建文件，当日文件名带日期。"""
    _fix_day(monkeypatch, "20261009")
    target = tmp_path / "nested" / "agents.log"
    log = AgentProcessLog(str(target))

    assert log.path == str(target)
    assert log.current_path() == tmp_path / "nested" / "agents-20261009.log"
    assert not log.current_path().exists()


@pytest.mark.unit
def test_default_path_is_cwd_logs(tmp_path, monkeypatch):
    """未注入落点时基路径为 `<当前工作目录>/logs/agents.log`。"""
    monkeypatch.chdir(tmp_path)

    assert resolve_log_path() == str(tmp_path / "logs" / "agents.log")
    assert (
        daily_log_file(resolve_log_path(), "20261009") == tmp_path / "logs" / "agents-20261009.log"
    )


@pytest.mark.unit
def test_write_creates_daily_file_and_fixed_columns(tmp_path, monkeypatch):
    """文件不存在则创建；每条记录六列（时间戳 | 角色 | 模型 | 任务与步骤 | 事件 | 内容）。"""
    _fix_day(monkeypatch, "20261009")
    log = AgentProcessLog(str(tmp_path / "logs" / "agents.log"))

    log.write(
        role="executor",
        model="deepseek-flash",
        scope="任务 12 · 步骤 3/8",
        event="思考",
        content="先看当前页面",
    )

    assert log.current_path().name == "agents-20261009.log"
    lines = log.current_path().read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    columns = lines[0].split(" | ")
    assert len(columns) == 6
    assert columns[1:] == [
        "executor",
        "deepseek-flash",
        "任务 12 · 步骤 3/8",
        "思考",
        "先看当前页面",
    ]
    assert len(columns[0]) == len("2026-10-09 10:22:44.123")


@pytest.mark.unit
def test_existing_content_is_appended_not_overwritten(tmp_path, monkeypatch):
    """再次写入（新实例 / 下一次运行）追加在既有内容之后，旧记录 MUST NOT 被覆盖。"""
    _fix_day(monkeypatch, "20261009")
    base = str(tmp_path / "agents.log")
    AgentProcessLog(base).write(
        role="planner",
        model="deepseek-flash",
        scope="任务 1 · 规划",
        event="思考",
        content="第一条",
    )
    AgentProcessLog(base).write(
        role="executor",
        model="deepseek-flash",
        scope="任务 1 · 步骤 1/2",
        event="思考",
        content="第二条",
    )

    lines = AgentProcessLog(base).current_path().read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert lines[0].endswith("第一条") and lines[1].endswith("第二条")
    assert "planner" in lines[0] and "executor" in lines[1]


@pytest.mark.unit
def test_day_switch_writes_new_file_and_keeps_old(tmp_path, monkeypatch):
    """跨零点：新记录进新一天的文件，旧文件内容原样保留。"""
    log = AgentProcessLog(str(tmp_path / "agents.log"))

    _fix_day(monkeypatch, "20261009")
    log.write(role="executor", model="m", scope="独立运行", event="思考", content="零点前")

    _fix_day(monkeypatch, "20261010")
    log.write(role="executor", model="m", scope="独立运行", event="思考", content="零点后")

    first = (tmp_path / "agents-20261009.log").read_text(encoding="utf-8")
    second = (tmp_path / "agents-20261010.log").read_text(encoding="utf-8")
    assert "零点前" in first and "零点后" not in first
    assert "零点后" in second and "零点前" not in second


@pytest.mark.unit
def test_history_files_are_not_removed(tmp_path, monkeypatch):
    """历史文件只增不删：写当天日志不会动到前几天留下的文件。"""
    _fix_day(monkeypatch, "20261010")
    history = tmp_path / "agents-20261008.log"
    history.write_text("历史记录\n", encoding="utf-8")

    AgentProcessLog(str(tmp_path / "agents.log")).write(
        role="executor", model="m", scope="独立运行", event="思考", content="今天"
    )

    assert history.read_text(encoding="utf-8") == "历史记录\n"


@pytest.mark.unit
def test_creation_and_switch_are_logged(tmp_path, monkeypatch, caplog):
    """首次创建与跨天切换各记一条 info，便于知道当前文件是哪个。"""
    log = AgentProcessLog(str(tmp_path / "agents.log"))

    with caplog.at_level(logging.INFO, logger=process_log_module.__name__):
        _fix_day(monkeypatch, "20261009")
        log.write(role="executor", model="m", scope="独立运行", event="思考", content="一")
        _fix_day(monkeypatch, "20261010")
        log.write(role="executor", model="m", scope="独立运行", event="思考", content="二")

    messages = [record.getMessage() for record in caplog.records]
    assert any("已创建" in message and "20261009" in message for message in messages)
    assert any("已切换到新一天" in message and "20261010" in message for message in messages)


@pytest.mark.unit
def test_scope_falls_back_to_standalone(tmp_path, monkeypatch):
    """没有任务上下文时，任务与步骤列如实写「独立运行」，不留空。"""
    _fix_day(monkeypatch, "20261009")
    log = AgentProcessLog(str(tmp_path / "agents.log"))
    log.write(role="planner", model="deepseek-flash", scope="", event="思考", content="拆步骤")

    assert log.current_path().read_text(encoding="utf-8").split(" | ")[3] == SCOPE_STANDALONE


@pytest.mark.unit
def test_newlines_are_flattened_and_long_content_truncated(tmp_path, monkeypatch):
    """内容压成单行（换行折叠为 ⏎）；超长按上限截断并标注。"""
    _fix_day(monkeypatch, "20261009")
    log = AgentProcessLog(str(tmp_path / "agents.log"), content_limit=20)

    log.write(role="executor", model="m", scope="独立运行", event="思考", content="第一行\n第二行")
    log.write(role="executor", model="m", scope="独立运行", event="思考", content="x" * 50)

    lines = log.current_path().read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "第一行 ⏎ 第二行" in lines[0]
    assert lines[1].endswith("…（截断，共 50 字）")


@pytest.mark.unit
def test_concurrent_writes_keep_one_record_per_line(tmp_path, monkeypatch):
    """多角色/多任务并发写同一文件：每条记录自成一行，不出现跨行交错。"""
    _fix_day(monkeypatch, "20261009")
    log = AgentProcessLog(str(tmp_path / "agents.log"))
    workers = 4
    per_worker = 25

    def _writer(index: int) -> None:
        for seq in range(per_worker):
            log.write(
                role=f"role{index}",
                model="deepseek-flash",
                scope="独立运行",
                event="思考",
                content=f"w{index}-{seq}",
            )

    threads = [threading.Thread(target=_writer, args=(i,)) for i in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    lines = log.current_path().read_text(encoding="utf-8").splitlines()
    assert len(lines) == workers * per_worker
    assert all(len(line.split(" | ")) == 6 for line in lines)
    assert {line.split(" | ")[1] for line in lines} == {f"role{i}" for i in range(workers)}
