"""角色过程日志：把三角色执行过程中的思考 / 工具调用 / 工具返回实时追加落盘。

记录格式为 `时间戳 | 角色 | 模型 | 任务与步骤 | 事件类型 | 内容`，内容换行折叠为 `⏎`；
文件按天切分（`agents-YYYYMMDD.log`），基路径由调用方注入，未注入时取
`<当前工作目录>/logs/agents.log`。写入自加锁，失败只记 warning，不打断模型执行。
"""

from __future__ import annotations

import json
import logging
import threading

from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "agents.log"
SCOPE_STANDALONE = "独立运行"
CONTENT_LIMIT = 2000
LINE_BREAK = " ⏎ "


def _today_stamp() -> str:
    """当天日期标记（YYYYMMDD）。"""
    return datetime.now().strftime("%Y%m%d")


def resolve_log_path(explicit: str = "") -> str:
    """过程日志基路径：显式值优先，为空时取 `<当前工作目录>/logs/agents.log`。

    Args:
        explicit: 调用方给出的基路径（可为空）。

    Returns:
        基路径字符串；实际写入文件由基路径按天派生。
    """
    value = str(explicit or "").strip()
    if value:
        return value
    return str(Path.cwd() / DEFAULT_LOG_DIR / DEFAULT_LOG_FILE)


def daily_log_file(base_path: str, stamp: str = "") -> Path:
    """基路径 + 当天日期 → 当天文件（形如 `agents-20261009.log`）。

    Args:
        base_path: 基路径。
        stamp: 日期标记；为空取当天。

    Returns:
        当天日志文件路径。
    """
    base = Path(str(base_path))
    suffix = base.suffix or ".log"
    return base.with_name(f"{base.stem}-{stamp or _today_stamp()}{suffix}")


class AgentProcessLog:
    """过程日志写入器：按天切分、追加写、自动建目录与文件、并发安全。"""

    def __init__(
        self,
        path: str = "",
        *,
        content_limit: int = CONTENT_LIMIT,
        enabled: bool = True,
    ) -> None:
        self.path = resolve_log_path(path)
        self.content_limit = int(content_limit)
        self.enabled = bool(enabled)
        self._lock = threading.Lock()
        self._prepared: set[str] = set()
        self._current = ""

    def current_path(self) -> Path:
        """当天实际写入的文件路径（跨零点后自动指向新一天）。"""
        return daily_log_file(self.path)

    def write(
        self,
        *,
        role: str,
        model: str,
        scope: str,
        event: str,
        content: object = "",
    ) -> None:
        """写一条记录（时间戳 | 角色 | 模型 | 任务与步骤 | 事件类型 | 内容）。"""
        if not self.enabled:
            return
        line = " | ".join(
            (
                self._stamp(),
                str(role or "-"),
                str(model or "-"),
                str(scope or SCOPE_STANDALONE),
                str(event or "-"),
                self._flatten(content),
            )
        )
        try:
            with self._lock:
                target = self.current_path()
                self._prepare(target)
                with open(target, "a", encoding="utf-8") as handle:
                    handle.write(line + "\n")
                    handle.flush()
        except Exception:  # noqa: BLE001 - 日志写入失败不得打断模型执行（已记 warning）
            logger.warning(
                "过程日志写入失败：%s（内容：%s）", self.path, self._flatten(content)[:200]
            )

    @staticmethod
    def _stamp() -> str:
        """当前北京时间，毫秒精度。"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def _flatten(self, content: object) -> str:
        """内容压成单行：换行折叠为 ⏎，超长按上限截断并标注。"""
        if isinstance(content, str):
            text = content
        else:
            text = json.dumps(content, ensure_ascii=False, default=str)
        text = text.replace("\r\n", "\n").replace("\n", LINE_BREAK).strip()
        if len(text) > self.content_limit:
            return f"{text[: self.content_limit]}…（截断，共 {len(text)} 字）"
        return text

    def _prepare(self, target: Path) -> None:
        """写入前建目录与文件；目标文件变化时记一条 info。"""
        key = str(target)
        if key in self._prepared:
            return
        if target.parent and not target.parent.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.touch()
        self._prepared.add(key)
        if key != self._current:
            switched = bool(self._current)
            self._current = key
            logger.info("过程日志%s：%s", "已切换到新一天的文件" if switched else "已创建", target)
