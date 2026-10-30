"""
文件名: ➡️ io_files.py 🏁
路径: ➡️ engines/utils/io_files.py 🏁
模块功能：➡️ 文件读写工具 🏁
说明：➡️ Python 调试运行入口： python -m engines.utils.io_files 🏁
时间：➡️ 2026-10-29 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间：➡️ 2026-10-29 🏁
类型: ➡️ 工具模块 🏁
简介说明:➡️ 
1. YAMLFileIO: YAML 文件读写
2. IniFileIO: INI 文件读取（configparser）
🏁
"""

from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Any

import yaml


def _resolve_path(file_path: str | Path) -> Path:
    """
    把路径规范成 Path：已是绝对路径则直接用；相对路径先按原样，不存在再拼当前工作目录。

    Args:
        file_path: 文件路径（str 或 Path）。

    Returns:
        解析后的 Path（不保证文件一定存在）。
    """
    path = Path(file_path)
    if path.is_absolute():
        return path
    if path.is_file():
        return path
    return Path.cwd() / path


class YAMLFileIO:
    """YAML 文件读写工具。"""

    @staticmethod
    def read_yaml(file_path: str | Path) -> Any:
        """
        读取 YAML 文件。

        Args:
            file_path: 文件路径。

        Returns:
            yaml.safe_load 的结果（常见为 dict）。

        Raises:
            FileNotFoundError: 文件不存在。
            OSError: 读文件失败。
            yaml.YAMLError: YAML 解析失败。
        """
        path = _resolve_path(file_path)
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def write_yaml(data: Any, file_path: str | Path, mode: str = "w") -> None:
        """
        写入 YAML 文件。

        Args:
            data: 要写入的数据。
            file_path: 文件路径。
            mode: 打开模式，默认覆盖写。
        """
        path = _resolve_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode, encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)


class IniFileIO:
    """INI 文件读取工具（标准库 configparser）。"""

    @staticmethod
    def read_ini(file_path: str | Path) -> ConfigParser:
        """
        读取 INI，返回 ConfigParser。

        保留选项名大小写（不转成小写），便于模型配置键原样使用。

        Args:
            file_path: INI 路径；相对路径相对当前工作目录（通常为仓库根）。

        Returns:
            已加载的 ConfigParser。

        Raises:
            FileNotFoundError: 文件不存在或未能读入。
        """
        path = _resolve_path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"INI 文件不存在: {path}")

        parser = ConfigParser()
        parser.optionxform = str  # 保留键名大小写
        loaded = parser.read(path, encoding="utf-8")
        if not loaded:
            raise FileNotFoundError(f"无法读取 INI: {path}")
        return parser

    @staticmethod
    def load_ini_as_dict(file_path: str | Path) -> dict[str, dict[str, str]]:
        """
        读取 INI 并转为嵌套字典：{section: {key: value}}。

        Args:
            file_path: INI 路径。

        Returns:
            各 section 的键值字典（值均为 str）。
        """
        parser = IniFileIO.read_ini(file_path)
        return {section: dict(parser.items(section)) for section in parser.sections()}

    @staticmethod
    def get(
        file_path: str | Path,
        section: str,
        option: str,
        fallback: str | None = None,
    ) -> str | None:
        """
        读取单个配置项。

        Args:
            file_path: INI 路径。
            section: 段名，如 agent_config。
            option: 键名，如 agent_config_file_path。
            fallback: 缺失时的默认值。

        Returns:
            配置值；段/键不存在时返回 fallback。
        """
        parser = IniFileIO.read_ini(file_path)
        if not parser.has_section(section) or not parser.has_option(section, option):
            return fallback
        return parser.get(section, option)



