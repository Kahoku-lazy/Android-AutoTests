"""平台智能体报告：磁盘上的报告列表与按名读取。

路径白名单：只接受「`<运行时间戳>/<文件名>`」两段结构，且解析后必须仍在报告根目录内。
不暴露任意路径读取能力。
"""

from __future__ import annotations

import re

from pathlib import Path

from engines.backend_bridge.reports import REPORT_ROOT

# 运行目录：<8 位日期>_<6 位时间>，记录器可能再追加 `_<角色>`；角色只允许字母数字下划线。
_RUN_PATTERN = re.compile(r"^\d{8}_\d{6}(?:_[A-Za-z0-9_]+)?$")
# 报告文件：<同名>.<html|jsonl>。
_FILE_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+\.(html|jsonl)$")

# 列表默认返回条数上限，避免一次扫太多目录。
_DEFAULT_LIMIT = 50


def _safe_target(run: str, name: str) -> Path:
    """
    把「运行目录 + 文件名」解析成绝对路径，并校验仍在报告根内。

    Args:
        run: 运行目录名。
        name: 文件名。

    Returns:
        解析后的绝对路径（文件可能不存在）。

    Raises:
        ValueError: 任一段不合白名单，或解析后越出报告根。
    """
    if not _RUN_PATTERN.match(run or ""):
        raise ValueError("运行目录名不合法")
    if not _FILE_PATTERN.match(name or ""):
        raise ValueError("报告文件名不合法")
    root = REPORT_ROOT.resolve()
    target = (root / run / name).resolve()
    if not target.is_relative_to(root):
        raise ValueError("报告路径越出根目录")
    return target


def _run_entry(run_dir: Path) -> dict:
    """
    把一个运行目录整理成一条列表项。

    Args:
        run_dir: 运行目录。

    Returns:
        含运行名、报告名、日志名、大小与修改时间的字典；没有 HTML 时报告名为空。
    """
    html = next(iter(sorted(run_dir.glob("*.html"))), None)
    log = next(iter(sorted(run_dir.glob("*.jsonl"))), None)
    return {
        "run": run_dir.name,
        "report": html.name if html else "",
        "log": log.name if log else "",
        "bytes": (html.stat().st_size if html else 0),
        "modified_at": (html.stat().st_mtime if html else run_dir.stat().st_mtime),
    }


def list_reports(*, limit: int = _DEFAULT_LIMIT) -> list[dict]:
    """
    列出最近的运行报告，新的在前。

    Args:
        limit: 最多返回多少条。

    Returns:
        列表项字典的列表；根目录不存在时返回空列表。
    """
    if not REPORT_ROOT.is_dir():
        return []
    runs = [
        item for item in REPORT_ROOT.iterdir() if item.is_dir() and _RUN_PATTERN.match(item.name)
    ]
    runs.sort(key=lambda item: item.name, reverse=True)
    return [_run_entry(item) for item in runs[: max(int(limit or 0), 0) or _DEFAULT_LIMIT]]


def read_report(run: str, name: str) -> tuple[str, str]:
    """
    读取一份报告文件的内容。

    Args:
        run: 运行目录名。
        name: 文件名。

    Returns:
        (文件名, 文本内容)。

    Raises:
        ValueError: 路径不在白名单内。
        FileNotFoundError: 文件不存在。
    """
    target = _safe_target(run, name)
    if not target.is_file():
        raise FileNotFoundError(f"报告不存在：{run}/{name}")
    return target.name, target.read_text(encoding="utf-8", errors="replace")
