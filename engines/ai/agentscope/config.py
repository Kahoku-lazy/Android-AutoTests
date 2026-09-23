"""配置层：模型连接配置 + 智能体提示词。设备执行专用。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """单个模型的连接配置（纯数据，供 create_model 建立连接）。"""

    provider: str = "deepseek"  # 提供商：deepseek / dashscope / openai / 自定义（走 OpenAI 兼容）
    model_name: str = ""  # 模型名（如 deepseek-v4-flash / qwen3.6-plus）
    api_key: str = ""  # 已解密的 API Key（Django 层解密后传入）
    base_url: str = ""  # 已解析的默认 base_url（provider_registry 解析）


@dataclass
class DeviceExecutionConfig:
    """设备执行三角色配置（规划 / 执行 / 验收）+ 每步最大重试次数。"""

    planner: ModelConfig = field(default_factory=ModelConfig)  # 规划模型连接
    executor: ModelConfig = field(default_factory=ModelConfig)  # 执行模型连接（多模态）
    verifier: ModelConfig = field(default_factory=ModelConfig)  # 验收模型连接（多模态）
    max_loops: int = 3  # 每步「执行↔验收」最大重试次数


# ── 智能体提示词（运行时由 Django 从 ai_agents.prompt_* 注入；此处留空不做回退）──

PLANNER_PROMPT = ""
VISION_PROMPT = ""
VERIFIER_PROMPT = ""


# ── 工具子集（按工具名匹配 TaskRequest.tools，供各智能体装配）──

# 设备规划模型工具：规划阶段读页面流文档（全量列表 + 单篇语义摘要）。
DEVICE_PLANNER_TOOLS = [
    "list_page_flows",
    "get_page_flow",
]

VISION_TOOLS = [
    "list_devices",
    "acquire_device",
    "release_device",
    "app_control",
    "tap_screen",
    "swipe_screen",
    "press_key",
    "input_text",
    "current_app",
    "click_ratio",
    "drag_ratio",
    "xpath_action",
    "list_apps",
    "screenshot_page",
]

VERIFIER_TOOLS = ["screenshot_page"]
