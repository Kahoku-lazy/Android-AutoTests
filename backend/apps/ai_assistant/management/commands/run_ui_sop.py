"""管理命令：跑一次平台 UI 执行 + 验收 SOP，并把 token 用量写进账本。

与 `run_ui_agent`（单角色）并列：单角色只管动手，本命令多一个验收者逐条核对。
SOP 不进对话页，平台侧用本命令触发。
"""

from __future__ import annotations

import asyncio

from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from backend.apps.usage_ledger.api import record_run_usages
from engines.backend_bridge.workflow import SPEC_KEYS, run_sop_once


class Command(BaseCommand):
    """跑一次执行 + 验收 SOP 并记录用量。"""

    help = "跑一次平台 UI 执行 + 验收 SOP，产出报告并把 token 用量写入账本"

    def add_arguments(self, parser: CommandParser) -> None:
        """声明参数。"""
        parser.add_argument("task", type=str, help="自然语言任务描述，写进流程的 task")
        parser.add_argument(
            "--spec",
            default="ui_task",
            choices=sorted(SPEC_KEYS),
            help="流程键：ui_task（通用）",
        )
        parser.add_argument("--model", default="", help="模型短名；留空用平台默认值")
        parser.add_argument(
            "--execution-id",
            default="",
            help="执行 ID，写进账本用于追溯；留空用本次报告的目录名",
        )

    def handle(self, *args: object, **options: object) -> None:
        """跑一次 SOP、写账、打印每步结论。"""
        del args
        task = str(options["task"])
        model_short = str(options.get("model") or "") or None

        result = asyncio.run(
            run_sop_once(
                task,
                spec_key=str(options.get("spec") or "ui_task"),
                model_short=model_short,
            )
        )
        execution_id = str(options.get("execution_id") or "")
        if not execution_id and result.report_path is not None:
            execution_id = Path(result.report_path).parent.name
        written = record_run_usages(
            result.usages,
            execution_id=execution_id,
            model=result.model,
        )

        self.stdout.write(self.style.SUCCESS("阶段：" + result.phase))
        for index, step in enumerate(result.steps, 1):
            mark = self.style.SUCCESS("通过") if step.passed else self.style.ERROR("未通过")
            self.stdout.write(f"  第 {index} 步 {step.subject}：{mark}（{step.attempts} 次尝试）")
            if step.message:
                self.stdout.write(f"    {step.message[:160]}")
        if result.report_path is not None:
            self.stdout.write("报告：" + str(result.report_path))
        self.stdout.write(
            "用量：输入 {0} · 输出 {1} · 缓存命中 {2} · 缓存写入 {3}".format(
                result.tokens.get("input", 0),
                result.tokens.get("output", 0),
                result.tokens.get("cache_hit", 0),
                result.tokens.get("cache_creation", 0),
            )
        )
        self.stdout.write("入账：{0} 条（execution_id={1}）".format(written, execution_id))
