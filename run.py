from __future__ import annotations

import argparse

from backend.config.env import load_dotenv
from utils.service_ctl import commands


def main() -> None:
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
