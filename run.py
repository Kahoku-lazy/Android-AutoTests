"""
模块功能：➡️ 平台管理入口：start/stop/restart/status/logs/check/setup，实现落在 utils.service_ctl 🏁
Python 调试：➡️ python -m run status 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（命令编排与测试见 utils/service_ctl 各模块头）
🏁
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
