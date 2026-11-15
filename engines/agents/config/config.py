"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/agents/config/config.py 🏁
模块功能：➡️ 配置读取与密钥加解密：全仓唯一读配置文件的地方 🏁
Python 调试：➡️ python -m engines.agents.config.config 🏁
时间：➡️ 2026-10-29 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. CONFIG_INI_PATH: 唯一的路径来源；所有配置路径都从 config.ini 读。
2. AGENT_CONFIG_PATH / MODEL_CONFIG_PATH: 两类配置路径，各自只定义一次、互不覆盖。
3. load_agent_config / load_model_config: 读文件；后者顺带把密钥加密成 SecretKey 注入条目。
4. SecretKey: 下游只拿密文对象，reveal() 时才在本模块内解密。
5. load_prompt_text / load_app_info_text / load_log_keyword_text: 读三类正文；消费方不再自己打开文件。
🏁
关联模块：➡️
1. engines.utils.io_files: 导入 IniFileIO / YAMLFileIO，读写统一走这里。
2. cryptography.fernet: 密钥加解密。
🏁
测试：➡️
1. 待功能定型后补：读表、缺密钥不阻断装载、加解密往返
🏁
"""

from __future__ import annotations

import os

from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from engines.utils.io_files import IniFileIO, YAMLFileIO

__all__ = [
    "AGENT_CONFIG_PATH",
    "CONFIG_INI_PATH",
    "MODEL_CONFIG_PATH",
    "SecretKey",
    "load_agent_config",
    "load_app_info_text",
    "load_log_keyword_text",
    "load_model_config",
    "load_prompt_text",
]

# ------------------------------------- 路径：唯一来源 config.ini -------------------------------------
CONFIG_INI_PATH = "engines/agents/config/config.ini"

ini_io = IniFileIO()

# 一个路径一个常量，只在这里出现一次；下面任何函数都不再重新定义或互相赋值。
AGENT_CONFIG_PATH = ini_io.get(CONFIG_INI_PATH, "agent_config", "agent_config_file_path")
MODEL_CONFIG_PATH = ini_io.get(CONFIG_INI_PATH, "model_config", "model_config_file_path")
_DATA_DIR = Path(__file__).resolve().parent / "data"
_PROMPTS_DIR = _DATA_DIR / "prompts"
_APP_INFO_DIR = _DATA_DIR / "app_info"
_LOG_KEYWORDS_DIR = _DATA_DIR / "log_keywords"


# ------------------------------------- 密钥加解密 -------------------------------------
# 进程内一把随机主键：明文只在 load_model_config 里出现一次，之后全域流转的都是密文。
_FERNET = Fernet(Fernet.generate_key())


def _encrypt(plain: str) -> str:
    """
    把明文密钥加密成密文。

    Args:
        plain: 明文密钥。

    Returns:
        可直接放进配置数据的密文字符串。
    """
    return _FERNET.encrypt(plain.encode("utf-8")).decode("utf-8")


def _decrypt(token: str) -> str:
    """
    把密文密钥还原成明文；只在本模块内部被 SecretKey 调用。

    Args:
        token: 密文字符串。

    Returns:
        明文密钥。

    Raises:
        ValueError: 密文非法或不属于本进程的主键。
    """
    try:
        return _FERNET.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("密钥密文非法：只能用本进程 config 加密出来的密文") from exc


class SecretKey:
    """
    加密后的模型密钥。

    下游（models / agent）只拿到这个对象，`repr` / `str` 永远打码；
    只有造客户端那一刻调用 `reveal()`，才算真正取到明文——而解密就发生在本模块里。

    Attributes:
        masked: 固定的打码文本。

    Raises:
        ValueError: 构造时密文与环境变量名同时为空。
    """

    __slots__ = ("_token", "_env_name")

    def __init__(self, token: str | None, *, env_name: str) -> None:
        """
        包装一份密文密钥。

        Args:
            token: 密文；None 表示该条目在装载时没配到密钥（环境变量为空）。
            env_name: 密钥来源的环境变量名，只用于报错。

        Raises:
            ValueError: token 与 env_name 都是空。
        """
        if token is None and not env_name:
            raise ValueError("SecretKey: 密文与环境变量名不能同时为空")
        self._token = token
        self._env_name = env_name

    @property
    def masked(self) -> str:
        """打码文本。

        Returns:
            固定为 `****`，不泄漏密文片段。
        """
        return "****"

    def reveal(self) -> str:
        """取明文密钥；只在构造模型凭证时调用。

        Returns:
            明文密钥。

        Raises:
            ValueError: 装载时没配到密钥（环境变量为空），或密文非法。
        """
        if self._token is None:
            raise ValueError(
                f"密钥未配置：条目缺少 api_key_env 或环境变量 {self._env_name} 未设置",
            )
        return _decrypt(self._token)

    def __repr__(self) -> str:
        """打码的开发者表示。

        Returns:
            形如 `SecretKey('****')`。
        """
        return f"SecretKey({self.masked!r})"

    def __str__(self) -> str:
        """打码的字符串形式。

        Returns:
            固定 `****`。
        """
        return self.masked

    def __bool__(self) -> bool:
        """是否已配到密钥。

        Returns:
            配到密钥返回 True。
        """
        return self._token is not None


# ------------------------------------- 读取配置 -------------------------------------
def _read_yaml(path: str | None, default: str) -> Any:
    """
    按「显式路径 > config.ini 里的默认值」读一个 YAML 文件。

    Args:
        path: 调用方显式传入的路径；空串表示没有。
        default: config.ini 里读到的默认路径。

    Returns:
        YAML 内容（常见为字典）。

    Raises:
        FileNotFoundError: 文件不存在。
        OSError: 读取失败。
        yaml.YAMLError: YAML 解析失败。
    """
    return YAMLFileIO.read_yaml(path or default)


def _safe_token(token: str, *, kind: str) -> str:
    """把配置文件名主干收成不含路径的一段。

    Args:
        token: 调用方给出的文件名主干。
        kind: 写进错误消息的配置种类。

    Returns:
        去掉首尾空白、补上 `.md` 的文件名。

    Raises:
        ValueError: token 为空，或含路径分隔符、换行。
    """
    if not isinstance(token, str) or not token.strip():
        raise ValueError(f"{kind} token 缺失或为空")
    text = token.strip()
    if "/" in text or "\\" in text or "\n" in text:
        raise ValueError(f"{kind} token 非法: {text!r}")
    return text if text.endswith(".md") else f"{text}.md"


def _read_text(directory: Path, name: str, *, missing: str) -> str:
    """读取配置目录下的一个 UTF-8 文本文件。

    Args:
        directory: 已登记的配置子目录。
        name: 已校验的文件名。
        missing: 文件不存在时的错误前缀。

    Returns:
        文件正文。

    Raises:
        FileNotFoundError: 文件不存在。
        OSError: 读取失败。
    """
    path = directory / name
    if not path.is_file():
        raise FileNotFoundError(f"{missing}: {path}")
    return path.read_text(encoding="utf-8")


def load_prompt_text(token: str) -> str:
    """按 token 读取提示词正文。

    Args:
        token: 无路径分隔符的文件名主干，如 UI_EXECUTOR_PROMPT。

    Returns:
        `config/data/prompts/{token}.md` 的正文。

    Raises:
        ValueError: token 非法。
        FileNotFoundError: 对应文件不存在。
        OSError: 读取失败。
    """
    return _read_text(_PROMPTS_DIR, _safe_token(token, kind="prompt"), missing="未找到提示词文件")


def load_app_info_text(token: str) -> str:
    """按 token 读取应用短卡正文。

    Args:
        token: 无路径分隔符的文件名主干，如 govee_home。

    Returns:
        `config/data/app_info/{token}.md` 的正文。

    Raises:
        ValueError: token 非法。
        FileNotFoundError: 对应文件不存在。
        OSError: 读取失败。
    """
    return _read_text(
        _APP_INFO_DIR, _safe_token(token, kind="app_info"), missing="未找到应用短卡文件"
    )


def load_log_keyword_text(sku: str) -> str:
    """按已校验的型号名读取日志关键词正文。

    Args:
        sku: 只含字母、数字、下划线和短横的型号名。

    Returns:
        对应 md 的正文。

    Raises:
        ValueError: 型号名含路径字符。
        FileNotFoundError: 文件不存在。
        OSError: 读取失败。
    """
    return _read_text(
        _LOG_KEYWORDS_DIR, _safe_token(sku, kind="log_keyword"), missing="未找到日志关键词文件"
    )


def load_agent_config(path: str | None = None) -> dict[str, Any]:
    """
    读取角色配置文件。

    Args:
        path: 角色配置路径；None 表示用 config.ini 里的 agent_config_file_path。

    Returns:
        文件内容（角色节字典）。

    Raises:
        FileNotFoundError: 文件不存在。
        OSError: 读取失败。
        yaml.YAMLError: YAML 解析失败。
    """
    return _read_yaml(path, AGENT_CONFIG_PATH)


def load_model_config(path: str | None = None) -> dict[str, Any]:
    """
    读取模型资产表，并为每条条目解析、加密密钥。

    读到后立刻把 `api_key_env` 指向的密钥加密成 `SecretKey` 注入条目；
    环境变量没配时不阻断装载，该条目的 SecretKey 为假值，创建模型时才报错。

    Args:
        path: 模型表路径；None 表示用 config.ini 里的 model_config_file_path。

    Returns:
        「短名 → 条目」；每条条目带 `api_key: SecretKey`。

    Raises:
        FileNotFoundError: 模型表不存在（由 YAMLFileIO 抛出）。
        OSError: 文件读取失败（由 YAMLFileIO 抛出）。
        yaml.YAMLError: YAML 解析失败（由 YAMLFileIO 抛出）。
        ValueError: 顶层不是映射表。
    """
    target = path or MODEL_CONFIG_PATH
    data = _read_yaml(path, MODEL_CONFIG_PATH)
    if not isinstance(data, dict):
        raise ValueError(f"{target}: 顶层必须是映射表，收到 {type(data).__name__}")

    resolved: dict[str, Any] = {}
    for name, raw in data.items():
        if not isinstance(raw, dict):
            # 形状问题留给 models 校验，不在读取层臆造结构。
            resolved[str(name)] = raw
            continue
        env_name = str(raw.get("api_key_env") or "").strip()
        plain = (os.environ.get(env_name, "") or "").strip() if env_name else ""
        resolved[str(name)] = {
            **raw,
            "api_key": SecretKey(_encrypt(plain) if plain else None, env_name=env_name),
        }
    return resolved
