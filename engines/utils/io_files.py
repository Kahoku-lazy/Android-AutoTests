from __future__ import annotations

from configparser import ConfigParser
from pathlib import Path
from typing import Any

import yaml


def _resolve_path(file_path: str | Path) -> Path:
    path = Path(file_path)
    if path.is_absolute():
        return path
    if path.is_file():
        return path
    return Path.cwd() / path


class YAMLFileIO:
    @staticmethod
    def read_yaml(file_path: str | Path) -> Any:
        path = _resolve_path(file_path)
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def write_yaml(data: Any, file_path: str | Path, mode: str = "w") -> None:
        path = _resolve_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode, encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)


class IniFileIO:
    @staticmethod
    def read_ini(file_path: str | Path) -> ConfigParser:
        path = _resolve_path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"INI 文件不存在: {path}")

        parser = ConfigParser()
        parser.optionxform = str
        loaded = parser.read(path, encoding="utf-8")
        if not loaded:
            raise FileNotFoundError(f"无法读取 INI: {path}")
        return parser

    @staticmethod
    def load_ini_as_dict(file_path: str | Path) -> dict[str, dict[str, str]]:
        parser = IniFileIO.read_ini(file_path)
        return {section: dict(parser.items(section)) for section in parser.sections()}

    @staticmethod
    def get(
        file_path: str | Path,
        section: str,
        option: str,
        fallback: str | None = None,
    ) -> str | None:
        parser = IniFileIO.read_ini(file_path)
        if not parser.has_section(section) or not parser.has_option(section, option):
            return fallback
        return parser.get(section, option)
