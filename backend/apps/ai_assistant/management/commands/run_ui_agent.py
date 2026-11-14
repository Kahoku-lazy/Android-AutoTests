"""管理命令：跑一次平台 UI 执行智能体，并把 token 用量写进账本。

平台目前没有 HTTP 触发口，先用命令打通「跑一次 → 出报告 → 入账」的整条链；
将来接入任务体系时，调用的是同一对函数（engines 侧运行入口 + 本命令里的入账两步）。
"""

from __future__ import annotations

import asyncio

from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from backend.apps.usage_ledger.api import record_run_usages
from engines.backend_bridge.run import run_ui_task


class Command(BaseCommand):
    """跑一次平台 UI 执行任务并记录用量。"""

    help = "跑一次平台 UI 执行智能体，产出报告并把 token 用量写入账本"

    def add_arguments(self, parser: CommandParser) -> None:
        """声明参数。"""
        parser.add_argument("task", type=str, help="自然语言任务描述")
        parser.add_argument("--model", default="", help="模型短名；留空用平台角色默认值")
        parser.add_argument(
            "--execution-id",
            default="",
            help="执行 ID，写进账本用于追溯；留空用本次报告的目录名",
        )

    def handle(self, *args: object, **options: object) -> None:
        """跑一次任务、写账、打印产物位置。"""
        del args
        task = str(options["task"])
        model_short = str(options.get("model") or "") or None

        result = asyncio.run(run_ui_task(task, model_short=model_short))
        execution_id = (
            str(options.get("execution_id") or "") or Path(result.report_path).parent.name
        )
        written = record_run_usages(
            result.usages,
            execution_id=execution_id,
            model=result.model,
        )

        self.stdout.write(self.style.SUCCESS("报告：" + str(result.report_path)))
        self.stdout.write(
            "用量：输入 {0} · 输出 {1} · 缓存命中 {2} · 缓存写入 {3}".format(
                result.tokens.get("input", 0),
                result.tokens.get("output", 0),
                result.tokens.get("cache_hit", 0),
                result.tokens.get("cache_creation", 0),
            )
        )
        self.stdout.write("入账：{0} 条（execution_id={1}）".format(written, execution_id))
