"""平台智能体报告：列表排序、路径白名单、读取。

只测 `ai_assistant/reports.py`。不测视图（另有用例）与运行入口。
目录命名对齐记录器的真实产出：目录 `YYYYmmdd_HHMMSS`，文件 `YYYYmmdd_HHMMSS_<角色>.html`。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.apps.ai_assistant import reports

pytestmark = [pytest.mark.unit]

ROLE = "ui_executor"
FIRST_RUN = "20261114_100000"
SECOND_RUN = "20261114_120000"


def _make_run(root: Path, run: str, *, html: bool = True) -> Path:
    """在给定根下造一个运行目录与产物，返回目录。"""
    run_dir = root / run
    run_dir.mkdir(parents=True)
    if html:
        (run_dir / f"{run}_{ROLE}.html").write_text("<html>ok</html>", encoding="utf-8")
    (run_dir / f"{run}_{ROLE}.jsonl").write_text("{}\n", encoding="utf-8")
    return run_dir


def test_list_reports_newest_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """按运行名倒序，新的在前，并给出报告名、日志名与大小。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path)
    _make_run(tmp_path, FIRST_RUN)
    _make_run(tmp_path, SECOND_RUN)

    items = reports.list_reports()

    assert [item["run"] for item in items] == [SECOND_RUN, FIRST_RUN]
    assert items[0]["report"] == f"{SECOND_RUN}_{ROLE}.html"
    assert items[0]["log"] == f"{SECOND_RUN}_{ROLE}.jsonl"
    assert items[0]["bytes"] > 0


def test_list_reports_ignores_unknown_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """不符合命名约定的目录不进入列表。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path)
    _make_run(tmp_path, FIRST_RUN)
    (tmp_path / "随便一个目录").mkdir()
    (tmp_path / "20261114_1000").mkdir()

    items = reports.list_reports()

    assert [item["run"] for item in items] == [FIRST_RUN]


def test_list_reports_accepts_role_suffixed_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """目录名带角色后缀时同样被接受（记录器将来若加后缀也不失效）。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path)
    _make_run(tmp_path, f"{FIRST_RUN}_{ROLE}")

    items = reports.list_reports()

    assert [item["run"] for item in items] == [f"{FIRST_RUN}_{ROLE}"]


def test_list_reports_missing_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """根目录不存在时返回空列表，不抛异常。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path / "not-created")
    assert reports.list_reports() == []


def test_read_report_returns_content(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """合法路径读回文件名与正文。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path)
    _make_run(tmp_path, FIRST_RUN)

    name, content = reports.read_report(FIRST_RUN, f"{FIRST_RUN}_{ROLE}.html")

    assert name.endswith(".html")
    assert "<html>" in content


def test_read_report_rejects_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """目录穿越与非法文件名一律拒绝。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path)

    with pytest.raises(ValueError):
        reports.read_report("..", "secret.html")
    with pytest.raises(ValueError):
        reports.read_report(FIRST_RUN, "../secret.html")
    with pytest.raises(ValueError):
        reports.read_report(FIRST_RUN, "report.txt")


def test_read_report_missing_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """白名单通过但文件不存在时抛 FileNotFoundError。"""
    monkeypatch.setattr(reports, "REPORT_ROOT", tmp_path)
    _make_run(tmp_path, FIRST_RUN, html=False)

    with pytest.raises(FileNotFoundError):
        reports.read_report(FIRST_RUN, f"{FIRST_RUN}_{ROLE}.html")
