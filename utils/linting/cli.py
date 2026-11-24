"""命令行入口：检查、导出，以及两个只用于审计的覆盖开关。"""

from __future__ import annotations

import argparse
import sys
import tomllib

from dataclasses import replace
from pathlib import Path

from utils.linting.checks import check
from utils.linting.config import CONFIG_NAME, load_config
from utils.linting.export import export
from utils.linting.model import Config
from utils.linting.report import render_json, render_text

EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_CONFIG_ERROR = 2


def emit(text: str, *, err: bool = False) -> None:
    """写一行到标准输出 / 标准错误，统一走 write 便于被当库引用时改向。"""
    stream = sys.stderr if err else sys.stdout
    stream.write(text + "\n")


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """命令行参数：检查模式或导出模式。"""
    parser = argparse.ArgumentParser(description="一份 .linting 驱动的模块依赖检查")
    parser.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--config", default="", help=f"配置文件路径（默认 <root>/{CONFIG_NAME}）")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument(
        "--check-type-checking",
        action="store_true",
        help="审计：把 TYPE_CHECKING 分支里的 import 也纳入检查（默认忽略）",
    )
    parser.add_argument(
        "--strict-indirect",
        action="store_true",
        help="审计：无视 allow_indirect_imports，按间接链检查全部合同",
    )
    subparsers = parser.add_subparsers(dest="command")
    export_parser = subparsers.add_parser("export", help="导出 tach.toml 与 .importlinter")
    export_parser.add_argument("--out-dir", default="", help="输出目录（默认配置文件所在目录）")
    return parser.parse_args(argv)


def apply_audit_overrides(config: Config, args: argparse.Namespace) -> Config:
    """按审计开关临时覆盖配置；只影响本次运行，不写回 .linting。"""
    forbids = config.forbids
    if args.strict_indirect:
        forbids = [replace(contract, allow_indirect=False) for contract in forbids]
    return replace(
        config,
        ignore_type_checking=config.ignore_type_checking and not args.check_type_checking,
        forbids=forbids,
    )


def main(argv: list[str] | None = None) -> int:
    """入口：读配置 → 检查或导出 → 按结果给退出码。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    root = Path(args.root).resolve()
    config_path = Path(args.config).resolve() if args.config else root / CONFIG_NAME

    try:
        config = load_config(config_path)
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        emit(f"配置错误：{exc}", err=True)
        return EXIT_CONFIG_ERROR

    if args.command == "export":
        out_dir = Path(args.out_dir).resolve() if args.out_dir else config.root
        try:
            written = export(config, out_dir)
        except OSError as exc:
            emit(f"导出失败：{exc}", err=True)
            return EXIT_CONFIG_ERROR
        for path in written:
            emit(f"已生成 {path}")
        return EXIT_OK

    if args.check_type_checking or args.strict_indirect:
        mode = "TYPE_CHECKING 内 import" if args.check_type_checking else "间接链"
        emit(f"[AUDIT] 本次按审计口径运行（含{mode}），结论不用于门禁判定。", err=True)
        config = apply_audit_overrides(config, args)

    try:
        report = check(config)
    except ValueError as exc:
        emit(f"配置错误：{exc}", err=True)
        return EXIT_CONFIG_ERROR
    emit(render_json(report) if args.json else render_text(report))
    return EXIT_OK if report.ok else EXIT_VIOLATION
