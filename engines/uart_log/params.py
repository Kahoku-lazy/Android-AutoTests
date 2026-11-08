"""
文件名: ➡ params.py 🏁
路径: ➡ engines/uart_log/params.py 🏁
模块功能：➡ 端口监测参数（不含波特率） 🏁
Python 调试：➡ python -m engines.uart_log.params 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. PortParams: 主机、端口、SKU、日志目录等监测参数
2. 波特率不在这里；检测和接收都不用它
🏁
关联模块：➡
1. 暂无本地 engines/utils 依赖
🏁
测试：➡
1. 暂无专门单测
🏁
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_LINE_LIMIT = 4096
DEFAULT_RETRY_SECONDS = 3.0


@dataclass(frozen=True)
class PortParams:
    """一次端口监测要用的参数。"""

    host: str
    port: int
    sku: str
    line_limit: int = DEFAULT_LINE_LIMIT
    retry_seconds: float = DEFAULT_RETRY_SECONDS
    log_directory: Path | None = None
