"""daphne 开发热重载入口 — 用 Django autoreload 包装 daphne（daphne 本身无 --reload）。

由 ``run.py start backend`` 调用；监控项目 .py 文件变化并自动重启进程，
避免改后端代码后手动 ``run.py restart backend``。

用法（等价 ``python -m daphne ...``，额外带热重载）：
    python run_daphne.py -p 8766 -b 0.0.0.0 config.asgi:application
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from daphne.cli import CommandLineInterface
from django.utils.autoreload import run_with_reloader


def main() -> None:
    """运行 daphne，参数（-p/-b/application）透传。"""
    CommandLineInterface().run(sys.argv[1:])


if __name__ == "__main__":
    run_with_reloader(main)
