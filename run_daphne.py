"""daphne 开发热重载入口 — 用 Django autoreload 包装 daphne（daphne 本身无 --reload）。

由 ``run.py start backend`` 调用；监控项目 .py 文件变化并自动重启进程，
避免改后端代码后手动 ``run.py restart backend``。

用法（等价 ``python -m daphne ...``，额外带热重载）：
    python run_daphne.py -p 8766 -b 0.0.0.0 config.asgi:application
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# autoreload 的父进程只做文件监控、不真正对外服务：标记出来，避免它在服务子进程之前
# 占住设备日志端口（日志端口同一时刻只能有一个监听者）。子进程必须把这个标记摘掉，
# 否则标记会随环境继承下去，服务进程反而也不采集。
if os.environ.get("RUN_MAIN") != "true":
    os.environ.setdefault("DJANGO_AUTORELOAD_PARENT", "1")
else:
    os.environ.pop("DJANGO_AUTORELOAD_PARENT", None)

import django

django.setup()

from daphne.cli import CommandLineInterface
from django.utils.autoreload import run_with_reloader


def main() -> None:
    """运行 daphne，参数（-p/-b/application）透传。"""
    CommandLineInterface().run(sys.argv[1:])


if __name__ == "__main__":
    run_with_reloader(main)
