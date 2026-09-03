"""UI 自动化流水线测试：python manage.py ui_pipeline "打开 govee 应用" [--serial RF8N21MSW7A]。

传入对话 → 三模型流水线（规划 → 执行 ↔ 验收）。真实控制设备，可能较慢。
"""

import asyncio
import json

from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.api import decrypt_key, get_platform_agent, get_provider_config
from apps.ai_assistant.engine_adapter import build_tool_specs
from engines.ai.agentscope.config import DeviceExecutionConfig, ModelConfig
from engines.ai.agentscope.model import DeviceExecution
from engines.ai.agentscope.workflow import DeviceExecutionWorkflow


def _build_device_execution(agent) -> DeviceExecution:
    route_cfg = (agent.route_configs or {}).get("device_control") or {}

    def _cfg(m: dict) -> ModelConfig:
        return ModelConfig(
            provider=m.get("provider", "deepseek"),
            model_name=m.get("model_name", ""),
            api_key=decrypt_key(m.get("api_key", "")),
            base_url=get_provider_config(m.get("provider", "deepseek"), m.get("base_url", ""))["base_url"],
        )

    config = DeviceExecutionConfig(
        planner=_cfg(route_cfg.get("planner") or {}),
        executor=_cfg(route_cfg.get("executor") or {}),
        verifier=_cfg(route_cfg.get("verifier") or {}),
        max_loops=int(agent.max_loops or 3),
    )
    return DeviceExecution(config, tools=build_tool_specs(), user_id=str(agent.owner_id or ""))


def _resolve_serial(specified: str) -> str:
    if specified:
        return specified
    from apps.device_pool.api import get_online_devices

    devices = get_online_devices()
    if not devices:
        raise CommandError("无在线设备，请用 --serial 指定")
    return devices[0].serial or ""


class Command(BaseCommand):
    help = "UI 自动化流水线测试：传入对话，规划→执行↔验收三模型流水线。"

    def add_arguments(self, parser):
        parser.add_argument("message", type=str, help="用户 UI 操作请求（对话）")
        parser.add_argument(
            "--serial",
            type=str,
            default="",
            help="目标设备 serial，默认取第一台在线设备",
        )

    def handle(self, *args, **options):
        message = (options["message"] or "").strip()
        if not message:
            raise CommandError("message 不能为空")

        agent = get_platform_agent()
        if agent is None:
            raise CommandError("未找到平台智能体")

        serial = _resolve_serial(options["serial"])
        dev = _build_device_execution(agent)
        workflow = DeviceExecutionWorkflow(dev, serial=serial)

        self.stdout.write(f"设备 serial：{serial}")
        self.stdout.write(f"输入请求：{message}")
        self.stdout.write("跑三模型流水线中…（规划 → 执行 ↔ 验收，可能较慢）\n")

        result = asyncio.run(workflow.run(message))

        self.stdout.write("\n========== 流水线结果 ==========")
        self.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
