"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/ae_harness/agents/config.py 🏁
模块功能：➡️ 读模型表与提示词正文 🏁
Python 调试：➡️ python -m engines.ae_harness.agents.config 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_models: 读整张模型表，返回短名到条目的映射。
2. load_prompt: 读一个提示词正文。
3. load_secret: 按环境变量名取密钥值，先查 .env，再查进程环境。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 yaml 与 dotenv。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor。
🏁
"""

from __future__ import annotations

import os

from pathlib import Path

import yaml

from dotenv import dotenv_values

_HERE = Path(__file__).resolve().parent
MODELS_PATH = _HERE / "config" / "models.yaml"
PROMPTS_DIR = _HERE / "config" / "prompts"
# 仓库根：engines/ae_harness/agents/config.py 往上三级。
_ENV_PATH = _HERE.parents[2] / ".env"
_ENV = dotenv_values(_ENV_PATH) if _ENV_PATH.exists() else {}


def load_models() -> dict:
    """
    读整张模型表。

    Returns:
        短名到条目字典的映射。
    """
    return yaml.safe_load(MODELS_PATH.read_text(encoding="utf-8"))


def load_prompt(name: str) -> str:
    """
    读一个提示词正文。

    Args:
        name: 提示词文件名，不带 .md。

    Returns:
        提示词正文。

    Raises:
        FileNotFoundError: 提示词文件不存在。
    """
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def load_secret(name: str) -> str:
    """
    按环境变量名取密钥值。

    Args:
        name: 环境变量名，如 DEEPSEEK_API_KEY。

    Returns:
        密钥值；两处都没配时返回空串。
    """
    return _ENV.get(name) or os.environ.get(name, "")
