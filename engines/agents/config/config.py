"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/agents/config/config.py 🏁
模块功能：➡️ Agent 配置加载 🏁
Python 调试：➡️ python -m engines.agents.config.config 🏁
时间：➡️ 2026-10-29 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_agent_config: 按顶层键读取 agent_config.yaml 中的一节
2. AGENT_CONFIG_FILE_PATH: 由 config.ini [agent_config] 指定
🏁
关联模块：➡️
1. engines.utils.io_files: 导入 YAMLFileIO, IniFileIO
🏁
测试：➡️
1. 暂无专门单测
🏁
"""

from typing import Any

from engines.utils.io_files import IniFileIO, YAMLFileIO

# ------------------------------------- agents 模块 全局配置文件 -------------------------------------
CONFIG_INI_PATH = "engines/agents/config/config.ini"

AGENT_CONFIG_FILE_PATH = IniFileIO.get(CONFIG_INI_PATH, "agent_config", "agent_config_file_path")


def _check_dict_not_empty(data: dict) -> bool:
    """
    校验参数是字典格式且不为空
    Args:
        data: 数据
    Returns:
        bool: 是否为字典格式且不为空
    """
    return isinstance(data, dict) and data is not {}


def _get_dict_value(data: dict, key: str) -> Any:
    """
    按点号路径取嵌套字典中的值。

    例如：_get_dict_value(data, "Credential.api_key_env") -> data["Credential"]["api_key_env"] -> "DEEPSEEK_API_KEY"。
    路径缺失、中途不是字典时返回 None。

    Args:
        data: 嵌套字典根节点。
        key: 点号分隔路径，如 "Credential.api_key_env"。

    Returns:
        路径对应的值；无法取到时为 None。
    """
    if not _check_dict_not_empty(data):
        return None
    if not isinstance(key, str) or not key.strip():
        return None

    current: Any = data
    for part in key.split("."):
        if not part or not isinstance(current, dict):
            return None
        if part not in current:
            return None
        current = current[part]
    return current


# ------------------------------------- 加载 Agent 配置 -------------------------------------
def load_agent_config(key: str, file_path: str = AGENT_CONFIG_FILE_PATH) -> dict:
    """
    按顶层键加载 agent_config.yaml 中的一节（如 UI_EXECUTOR_ROLE_CONFIG）。

    Args:
        key: YAML 顶层键名。
        file_path: YAML 路径；默认读 config.ini 中的 agent_config_file_path。

    Returns:
        该节的字典；节缺失或文件为空时返回空 dict。
    """
    config = YAMLFileIO.read_yaml(file_path)
    if _check_dict_not_empty(config):
        return _get_dict_value(config, key)
    return {}


# 兼容旧名
MODEL_CONFIG_FILE_PATH = AGENT_CONFIG_FILE_PATH
load_models_config = load_agent_config
