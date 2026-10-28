"""
python -m 调试路径: backend.apps.knowledge_assistant.runtime

本模块的业务功能如下：
1. session_log_dir(): 解析知识库助手对话日志目录。
2. build_status_payload(): 把引擎就绪状态与本地日志路径合成 HTTP 响应体。

本模块只做后端接入层的配置拼装；实时模型与 AgentScope 配置在
engines.agents.realtime_vocie.config。
"""

from __future__ import annotations

import os

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from engines.agents.realtime_vocie.config import build_runtime_status

from .transcript_log import describe_path, today_file

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
DEFAULT_LOG_DIR: Final[Path] = REPO_ROOT / "logs" / "knowledge_assistant"


def _read(environ: Mapping[str, str] | None, name: str) -> str:
    """读取一个配置项：显式传入的映射优先，否则读进程环境变量。"""
    value = environ.get(name) if environ is not None else os.environ.get(name)
    return (value or "").strip()


def session_log_dir(
    environ: Mapping[str, str] | None = None,
    *,
    base_dir: Path | None = None,
) -> Path:
    """
    解析对话日志目录；相对路径按仓库根目录展开。

    Args:
        environ: 测试注入的配置映射。
        base_dir: 相对路径的基准目录；默认仓库根目录。

    Returns:
        绝对路径形式的日志目录（不保证已存在）。
    """
    raw = _read(environ, "KNOWLEDGE_ASSISTANT_LOG_DIR")
    root = (base_dir or REPO_ROOT).resolve()
    if not raw:
        return (root / "logs" / "knowledge_assistant").resolve()
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def build_status_payload(environ: Mapping[str, str] | None = None) -> dict:
    """
    生成状态接口的响应体，不包含任何密钥。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        含 enabled / ready / reason / model / voice / agent_name / log_dir / log_file 的字典。
    """
    status = build_runtime_status(environ)
    log_dir = session_log_dir(environ)
    return {
        **status,
        "log_dir": describe_path(log_dir),
        "log_file": describe_path(today_file(log_dir)),
    }
