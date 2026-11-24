"""平台启停工具包：`run.py` 的命令实现（配置 / 进程 / 数据库 / 服务 / 命令编排）。

分层单向向下，禁止反向 import：
`commands -> services -> {db, proc} -> config`。
"""

from __future__ import annotations
