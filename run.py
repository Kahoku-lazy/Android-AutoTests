"""Android-AutoTests platform manager — start / stop / restart / status / logs / check.

Usage:
    python run.py start [backend|frontend ...] [--no-db]
    python run.py stop  [backend|frontend ...]
    python run.py restart [...] [--no-db]
    python run.py status
    python run.py logs [backend|frontend ...]
    python run.py check          # 本地质量门禁（实现见 utils/check_gates.py）
    python run.py setup          # 安装项目内 platform-tools（唯一会联网的命令）
    python run.py setup --check  # 只检测 adb，缺失时退出码 1

本文件只做入口：加载 .env、解析参数、分发命令。命令实现在 utils/service_ctl/。
"""

from __future__ import annotations

import argparse

from backend.config.env import load_dotenv
from utils.service_ctl import commands


def main() -> None:
    """加载 .env 后按子命令分发到 utils.service_ctl.commands。"""
    load_dotenv()
    parser = argparse.ArgumentParser(description="Android-AutoTests platform manager")
    parser.add_argument(
        "cmd", choices=["start", "stop", "restart", "status", "logs", "check", "setup"]
    )
    parser.add_argument("services", nargs="*", default=[], help="backend frontend (default: all)")
    parser.add_argument("--check", action="store_true", help="setup: 只检测，不下载")
    parser.add_argument("--force", action="store_true", help="setup: 强制重装 platform-tools")
    parser.add_argument(
        "--from-file", default=None, help="setup: 用本地 platform-tools zip 离线安装"
    )
    parser.add_argument("--no-db", action="store_true", help="start/restart: 跳过数据库检查")
    args = parser.parse_args()

    {
        "start": lambda: commands.cmd_start(args.services, skip_db=args.no_db),
        "stop": lambda: commands.cmd_stop(args.services),
        "restart": lambda: commands.cmd_restart(args.services, skip_db=args.no_db),
        "status": commands.cmd_status,
        "logs": lambda: commands.cmd_logs(args.services),
        "check": commands.cmd_check,
        "setup": lambda: commands.cmd_setup(args.check, args.force, args.from_file),
    }[args.cmd]()


if __name__ == "__main__":
    main()
