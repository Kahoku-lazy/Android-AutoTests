"""三模型分阶段测试：python manage.py model_test <stage> "<输入>" [--serial ...]

stage ∈ {planner, executor, verifier, full}：

  planner   规划模型：输入用户需求 → 输出 plans（目标 / 步骤 / 验收标准）
  executor  执行模型：输入步骤 → 在设备上执行 → 输出执行结果
  verifier  验收模型：输入验收标准 → 截图二次确认 → 输出 pass/fail
  full      完整流程：新建任务 → 规划 → 执行 ↔ 验收（三模型完整跑一遍，结果落库）

示例：
  python manage.py model_test planner "启动 govee 应用并进入设备列表"
  python manage.py model_test verifier "前台 package 应为 govee 包名" --serial RF8N21MSW7A
  python manage.py model_test full "启动 govee 应用并进入设备列表" --serial RF8N21MSW7A
"""

import asyncio
import json
import logging

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.api import (
    create_task,
    decrypt_key,
    finalize_task,
    get_platform_agent,
    get_provider_config,
)
from apps.ai_assistant.engine_adapter import build_tool_specs
from apps.ai_assistant.skills_catalog import list_enabled_skill_dirs
from engines.ai.agentscope.config import DeviceExecutionConfig, ModelConfig
from engines.ai.agentscope.model import build_device_models
from engines.ai.agentscope.workflow import (
    DeviceExecutionWorkflow,
    _parse_json,
)

logger = logging.getLogger("ai_assistant.model_test")


def _setup_logging() -> None:
    """配置日志到 logs/AI-MODEL-TEST.log（幂等，避免重复叠加 handler）。

    挂在 ai_assistant 根 logger 上，使 workflow 的 ai_assistant.workflow 子 logger
    也写入同一文件。
    """
    root = logging.getLogger("ai_assistant")
    if root.handlers:
        return
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    handler = logging.FileHandler(log_dir / "AI-MODEL-TEST.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    root.propagate = False


def _build_device_models(agent):
    """按智能体配置装配三个角色模型，返回 (config, planner, executor, verifier)。"""
    route_cfg = (agent.route_configs or {}).get("device_control") or {}

    def _cfg(m: dict) -> ModelConfig:
        return ModelConfig(
            provider=m.get("provider", "deepseek"),
            model_name=m.get("model_name", ""),
            api_key=decrypt_key(m.get("api_key", "")),
            base_url=get_provider_config(m.get("provider", "deepseek"), m.get("base_url", ""))[
                "base_url"
            ],
        )

    config = DeviceExecutionConfig(
        planner=_cfg(route_cfg.get("planner") or {}),
        executor=_cfg(route_cfg.get("executor") or {}),
        verifier=_cfg(route_cfg.get("verifier") or {}),
        max_loops=int(agent.max_loops or 3),
    )
    planner, executor, verifier = build_device_models(
        config,
        tools=build_tool_specs(),
        user_id=str(agent.owner_id or ""),
        skill_dirs=list_enabled_skill_dirs() if agent.enable_skills else [],
    )
    return config, planner, executor, verifier


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
            f"route_configs.device_control.{name} 的模型名"
        )
    if not cfg.api_key:
        raise CommandError(f"「{name}」的 api_key 未配置，请到智能体配置页填写 API Key")


class Command(BaseCommand):
    help = "三模型分阶段测试：验证规划/执行/验收模型的输入输出。"

    def add_arguments(self, parser):
        parser.add_argument("stage", type=str, choices=["planner", "executor", "verifier", "full"])
        parser.add_argument("input", type=str, help="输入内容")
        parser.add_argument(
            "--serial", type=str, default="", help="设备 serial（executor/verifier 用）"
        )

    def handle(self, *args, **options):
        _setup_logging()
        stage = options["stage"]
        text = (options["input"] or "").strip()
        if not text:
            raise CommandError("input 不能为空")

        agent = get_platform_agent()
        if agent is None:
            raise CommandError("未找到平台智能体")

        config, planner, executor, verifier = _build_device_models(agent)
        serial = _resolve_serial(options["serial"])

        # 前置校验：仅校验本次要测的那个模型，避免跑到 deepseek 才报 400
        if stage == "planner":
            _check_model(config.planner, "规划模型(planner)")
        elif stage == "executor":
            _check_model(config.executor, "执行模型(executor)")
        elif stage == "verifier":
            _check_model(config.verifier, "校验模型(verifier)")
        elif stage == "full":
            _check_model(config.planner, "规划模型(planner)")
            _check_model(config.executor, "执行模型(executor)")
            _check_model(config.verifier, "校验模型(verifier)")

        if stage == "planner":
            logger.info("【planner 阶段】输入 user_input=%r", text)
            self.stdout.write("=" * 60)
            self.stdout.write("【规划模型】输入：")
            self.stdout.write(text)
            self.stdout.write("-" * 60)
            result = asyncio.run(planner.run(text))
            out = _parse_json(result.output)
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
            self.stdout.write(f"【执行模型】serial={serial or '（未指定/无在线设备）'} 输入步骤：")
            self.stdout.write(text)
            self.stdout.write("-" * 60)
            result = asyncio.run(executor.run(serial, text, 1, 1))
            out = _parse_json(result.output)
            logger.info(
                "【executor 阶段】输出 %s",
                json.dumps(out, ensure_ascii=False) if out else "未返回结构化输出",
            )
            self.stdout.write("输出（执行结果）：")
            self.stdout.write(
                json.dumps(out, ensure_ascii=False, indent=2) if out else "未返回结构化输出"
            )

        elif stage == "verifier":
            logger.info("【verifier 阶段】serial=%s 输入 verification=%r", serial, text)
            self.stdout.write("=" * 60)
            self.stdout.write(
                f"【验收模型】serial={serial or '（未指定/无在线设备）'} 输入验收标准："
            )
            self.stdout.write(text)
            self.stdout.write("-" * 60)
            result = asyncio.run(verifier.run(serial, text, 1, 1, "", ""))
            out = _parse_json(result.output)
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
                f"【完整流程】serial={serial or '（未指定/无在线设备）'} 输入：{text}"
            )

            # 新建任务
            task = create_task(
                agent,
                title=text[:100],
                goal=text,
                device_serial=serial,
            )
            self.stdout.write(f"已新建任务 id={task.id}")

            # 跑完整工作流：规划 → 执行 ↔ 验收
            workflow = DeviceExecutionWorkflow(planner, executor, verifier, config, serial=serial)
            result = asyncio.run(workflow.run(text))
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
