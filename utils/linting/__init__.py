"""模块依赖检查（配置：仓库根 `.linting`）。

允许清单回答“每个包可以依赖谁”，禁止合同回答“谁绝不许依赖谁”。
门禁名为 `linting`，入口 `python -m utils.linting`；规则说明见 `.agents/lint/linting.md`。
"""

from utils.linting.checks import check
from utils.linting.cli import main
from utils.linting.config import CONFIG_NAME, load_config

__all__ = ["CONFIG_NAME", "check", "load_config", "main"]
