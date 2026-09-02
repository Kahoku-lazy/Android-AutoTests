"""平台任务分阶段测试：python manage.py platform_task_test <stage> "<输入>" [--serial ...]

stage ∈ {planner, executor, verifier, full}：

  planner   规划模型：输入用户需求 → 判断职责①~④ → 输出 plans（目标 / 步骤 / 验收标准）
  executor  执行模型：输入步骤 → 用平台工具完成 → 输出执行结果
  verifier  验收模型：输入验收标准 → 查询工具二次确认 → 输出 pass/fail + completed/failed
  full      完整流程：新建平台任务 → 规划 → 执行 ↔ 验收（三模型完整跑一遍，结果落库）

示例：
  python manage.py platform_task_test planner "探索 govee 应用并保存元素定位"
  python manage.py platform_task_test full "基于页面流生成 govee 用例" --serial RF8N21MSW7A
  python manage.py platform_task_test full "执行用例集" --requirements "..." --checklist "..." --report-name "..."
"""

import asyncio
import json
import logging

from pathlib import Path

from agentscope.message import UserMsg
from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.agent_scope.config import ModelConfig, PlatformTaskConfig
from apps.ai_assistant.agent_scope.model import PlatformTask
from apps.ai_assistant.agent_scope.workflow import (
    PlannerOutput,
    PlatformTaskWorkflow,
    VerificationResult,
)
from apps.ai_assistant.api import create_task, decrypt_key, finalize_task, get_platform_agent

logger = logging.getLogger("ai_assistant.platform_task_test")


def _setup_logging() -> None:
    """配置日志到 logs/AI-PLATFORM-TASK-TEST.log（幂等，避免重复叠加 handler）。"""
    root = logging.getLogger("ai_assistant")
    if root.handlers:
        return
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_dir / "AI-PLATFORM-TASK-TEST.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    root.propagate = False


def _build_platform_task(agent) -> PlatformTask:
    route_cfg = (agent.route_configs or {}).get("platform_task") or {}

    def _cfg(m: dict) -> ModelConfig:
        return ModelConfig(
            provider=m.get("provider", "deepseek"),
            model_name=m.get("model_name", ""),
            api_key=decrypt_key(m.get("api_key", "")),
            base_url=m.get("base_url", ""),
        )

    config = PlatformTaskConfig(
        planner=_cfg(route_cfg.get("planner") or {}),
        executor=_cfg(route_cfg.get("executor") or {}),
        verifier=_cfg(route_cfg.get("verifier") or {}),
        max_loops=int(agent.max_loops or 3),
    )
    return PlatformTask(config, user_id=str(agent.owner_id or ""))


def _resolve_serial(specified: str) -> str:
    if specified:
        return specified
    from apps.device_pool.api import get_online_devices

    devices = get_online_devices()
    if not devices:
        return ""
    return devices[0].serial or ""


def _check_model(cfg: ModelConfig, name: str) -> None:
    """前置校验：model_name / api_key 为空时直接报清晰中文错误。"""
    if not cfg.model_name:
        raise CommandError(
            f"「{name}」的 model_name 未配置，请到智能体配置页填写 "
            f"route_configs.platform_task.{name} 的模型名"
        )
    if not cfg.api_key:
        raise CommandError(f"「{name}」的 api_key 未配置，请到智能体配置页填写 API Key")


def _msg_text(msg) -> str:
    content = msg.content
    if isinstance(content, str):
        return content
    return "".join(getattr(b, "text", "") for b in (content or []))


class Command(BaseCommand):
    help = "平台任务分阶段测试：验证规划/执行/验收模型的输入输出。"

    def add_arguments(self, parser):
        parser.add_argument("stage", type=str, choices=["planner", "executor", "verifier", "full"])
        parser.add_argument("input", type=str, help="输入内容")
        parser.add_argument("--serial", type=str, default="", help="设备 serial（职责①④借道用）")
        parser.add_argument("--requirements", type=str, default="", help="任务要求（full 用）")
        parser.add_argument("--checklist", type=str, default="", help="校验清单（full 用）")
        parser.add_argument("--report-name", type=str, default="", help="报告文件名（full 用）")

    def handle(self, *args, **options):
        _setup_logging()
        stage = options["stage"]
        text = (options["input"] or "").strip()
        if not text:
            raise CommandError("input 不能为空")

        agent = get_platform_agent()
        if agent is None:
            raise CommandError("未找到平台智能体")

        pt = _build_platform_task(agent)
        serial = _resolve_serial(options["serial"])

        # 前置校验：仅校验本次要测的那个模型，避免跑到 deepseek 才报 400
        if stage == "planner":
            _check_model(pt.config.planner, "规划模型(planner)")
        elif stage == "executor":
            _check_model(pt.config.executor, "执行模型(executor)")
        elif stage == "verifier":
            _check_model(pt.config.verifier, "校验模型(verifier)")
        elif stage == "full":
            _check_model(pt.config.planner, "规划模型(planner)")
            _check_model(pt.config.executor, "执行模型(executor)")
            _check_model(pt.config.verifier, "校验模型(verifier)")

        if stage == "planner":
            logger.info("【planner 阶段】输入 user_input=%r", text)
            self.stdout.write("=" * 60)
            self.stdout.write("【平台规划模型】输入：")
            self.stdout.write(text)
            self.stdout.write("-" * 60)
            msg = asyncio.run(
                pt.planner_agent.reply(
                    UserMsg(name="user", content=text),
                    structured_schema=PlannerOutput,
                )
            )
            out = msg.structured_output
            logger.info(
                "【planner 阶段】输出 plans=%s",
                json.dumps(out, ensure_ascii=False) if out else "未返回结构化输出",
            )
            self.stdout.write("输出（结构化）：")
            self.stdout.write(
                json.dumps(out, ensure_ascii=False, indent=2) if out else "未返回结构化输出"
            )

        elif stage == "executor":
            logger.info("【executor 阶段】serial=%s 输入 steps=%r", serial, text)
            self.stdout.write("=" * 60)
            self.stdout.write(
                f"【平台执行模型】serial={serial or '（未指定/无在线设备）'} 输入步骤："
            )
            self.stdout.write(text)
            self.stdout.write("-" * 60)
            prompt = f"请完成以下目标的步骤：\n{text}"
            if serial:
                prompt = f"设备 serial：{serial}\n{prompt}"
            msg = asyncio.run(pt.executor_agent.reply(UserMsg(name="user", content=prompt)))
            result = _msg_text(msg)
            logger.info("【executor 阶段】输出 result=%s", result or "（无文本输出）")
            self.stdout.write("输出（执行结果）：")
            self.stdout.write(result or "（无文本输出）")

        elif stage == "verifier":
            logger.info("【verifier 阶段】输入 verification=%r", text)
            self.stdout.write("=" * 60)
            self.stdout.write("【平台验收模型】输入验收标准：")
            self.stdout.write(text)
            self.stdout.write("-" * 60)
            prompt = f"验收标准：{text}\n请用查询工具二次确认是否达成验收标准。"
            msg = asyncio.run(
                pt.verifier_agent.reply(
                    UserMsg(name="user", content=prompt),
                    structured_schema=VerificationResult,
                )
            )
            out = msg.structured_output
            logger.info(
                "【verifier 阶段】输出 %s",
                json.dumps(out, ensure_ascii=False) if out else "未返回结构化输出",
            )
            self.stdout.write("输出（验收结果）：")
            self.stdout.write(
                json.dumps(out, ensure_ascii=False, indent=2) if out else "未返回结构化输出"
            )

        elif stage == "full":
            logger.info("【full 阶段】serial=%s 输入 user_input=%r", serial, text)
            self.stdout.write("=" * 60)
            self.stdout.write(
                f"【平台完整流程】serial={serial or '（未指定/无在线设备）'} 输入：{text}"
            )

            # 新建任务
            task = create_task(
                agent,
                title=text[:100],
                goal=text,
                route="platform_task",
                requirements=options["requirements"],
                checklist=options["checklist"],
                report_name=options["report_name"],
                device_serial=serial,
            )
            self.stdout.write(f"已新建任务 id={task.id}")

            # 跑完整工作流：规划 → 执行 ↔ 验收
            workflow = PlatformTaskWorkflow(pt, serial=serial)
            result = asyncio.run(
                workflow.run(
                    text,
                    requirements=options["requirements"],
                    checklist=options["checklist"],
                    report_name=options["report_name"],
                )
            )
            logger.info("【full 阶段】最终结果 status=%s", result.get("status"))

            # 更新任务状态 + 结果 + token 用量（走 api，与任务发布同口径）
            status = "completed" if result.get("status") == "success" else "failed"
            finalize_task(
                task,
                status=status,
                result=json.dumps(result, ensure_ascii=False),
                usage=result.get("usage"),
            )

            self.stdout.write("-" * 60)
            self.stdout.write("完整流程结果：")
            self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
            self.stdout.write(f"任务 #{task.id} 状态：{task.status}")
