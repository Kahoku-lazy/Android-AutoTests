"""
文件名: ➡️ role_sys_prompts.py 🏁
路径: ➡️ engines/agents/role_sys_prompts.py 🏁
模块功能：➡️ 角色系统提示词与模型能力目录的唯一脚本入口 🏁
Python 调试：➡️ python -m engines.agents.role_sys_prompts 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_prompt_md: 按 token 读取 config/data/prompts/{token}.md（UTF-8）
2. resolve_system_prompt: 解析 RoleConfig.system_prompt：多行正文原样；短 token 读 md
3. load_app_info_md / with_app_info: 按 token 读 config/data/app_info/{token}.md，追加「被测应用短卡」
4. UiControlPrompts: UI 控制（设备操作）提示词：执行 / 验收
5. CaseAuthoringPrompts: 用例编写提示词：规划 / 编写 / 验收（含 Goal 变体）
6. VoiceKnowledgePrompts: 知识库 Omni 语音助手系统提示词
7. build_system_prompt: 兼容 realtime_vocie.knowledge：返回语音助手系统提示词
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_prompts.py: 家电测试用例编写/验收提示词的纪律断言
2. tests/graybox/unit/test_case_authoring_roles.py: 家电测试用例编写/验收角色的装配与成对运行入口
3. tests/graybox/unit/test_role_prompt_guardrails.py: 角色提示词纪律断言：把复盘出的可避免失败写成不可回退的文本约束
🏁
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

_PROMPTS_DIR: Final[Path] = Path(__file__).resolve().parent / "config" / "data" / "prompts"
_APP_INFO_DIR: Final[Path] = Path(__file__).resolve().parent / "config" / "data" / "app_info"


def load_prompt_md(token: str) -> str:
    """按 token 读取 config/data/prompts/{token}.md（UTF-8）。

    Args:
        token: 无路径分隔符的文件名主干，如 UI_EXECUTOR_PROMPT。

    Returns:
        文件正文。

    Raises:
        ValueError: token 非法。
        FileNotFoundError: 对应 md 不存在。
    """
    if not isinstance(token, str) or not token.strip():
        raise ValueError("prompt token 缺失或为空")
    text = token.strip()
    if "/" in text or "\\" in text or "\n" in text:
        raise ValueError(f"prompt token 非法: {text!r}")
    name = text if text.endswith(".md") else f"{text}.md"
    path = _PROMPTS_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"未找到提示词文件: {path}")
    return path.read_text(encoding="utf-8")


def resolve_system_prompt(raw: object, *, where: str = "system_prompt") -> str:
    """解析 RoleConfig.system_prompt：多行正文原样；短 token 读 md。"""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{where} 缺失或为空")
    if "\n" in raw:
        return raw
    text = raw.strip()
    if "/" in text or "\\" in text:
        return text
    try:
        return load_prompt_md(text)
    except FileNotFoundError as exc:
        expected = _PROMPTS_DIR / (text if text.endswith(".md") else f"{text}.md")
        raise FileNotFoundError(
            f"{where}={text!r} 未找到提示词文件，期望路径: {expected}",
        ) from exc


def load_app_info_md(token: str) -> str:
    """按 token 读取 config/data/app_info/{token}.md（UTF-8）。

    Args:
        token: 无路径分隔符的文件名主干，如 govee_home。

    Returns:
        文件正文。

    Raises:
        ValueError: token 非法。
        FileNotFoundError: 对应 md 不存在。
    """
    if not isinstance(token, str) or not token.strip():
        raise ValueError("app_info token 缺失或为空")
    text = token.strip()
    if "/" in text or "\\" in text or "\n" in text:
        raise ValueError(f"app_info token 非法: {text!r}")
    name = text if text.endswith(".md") else f"{text}.md"
    path = _APP_INFO_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"未找到应用短卡文件: {path}")
    return path.read_text(encoding="utf-8")


def with_app_info(system_prompt: str, app_info_token: object | None) -> str:
    """若配置了 app_info token，在系统提示词末尾追加「被测应用短卡」正文。

    Args:
        system_prompt: 已解析的角色系统提示词正文。
        app_info_token: YAML RoleConfig.app_info；None / 空则原样返回。

    Returns:
        原提示词，或追加短卡后的提示词。
    """
    if app_info_token is None:
        return system_prompt
    if not isinstance(app_info_token, str) or not app_info_token.strip():
        return system_prompt
    card = load_app_info_md(app_info_token).strip()
    if not card:
        return system_prompt
    base = system_prompt.rstrip()
    return f"{base}\n\n## 被测应用短卡\n{card}\n"


# 每轮用户输入末尾追加的硬要求：系统提示词约束一次，逐轮再提醒一次。
CHINESE_DEMAND = (
    "\n\n（硬性要求：本次的思考过程与回复必须使用中文；输出契约里的 JSON 字段名保持英文。）"
)


class UiControlPrompts:
    """UI 控制（设备操作）提示词：执行 / 验收。"""

    EXECUTOR_TOKEN = "UI_EXECUTOR_PROMPT"
    VERIFIER_TOKEN = "UI_VERIFIER_PROMPT"

    @classmethod
    def executor(cls) -> str:
        """UI 控制执行角色系统提示词正文。"""
        return load_prompt_md(cls.EXECUTOR_TOKEN)

    @classmethod
    def verifier(cls) -> str:
        """UI 控制验收角色系统提示词正文。"""
        return load_prompt_md(cls.VERIFIER_TOKEN)


class CaseAuthoringPrompts:
    """用例编写提示词：规划 / 编写 / 验收（含 Goal 变体）。"""

    PLANNER_TOKEN = "CASE_MODULE_PLANNER_PROMPT"
    WRITER_TOKEN = "CASE_WRITER_PROMPT"
    WRITER_GOAL_TOKEN = "CASE_WRITER_GOAL_PROMPT"
    VERIFIER_TOKEN = "CASE_VERIFIER_PROMPT"
    VERIFIER_GOAL_TOKEN = "CASE_VERIFIER_GOAL_PROMPT"

    @classmethod
    def planner(cls) -> str:
        """用例编写规划角色系统提示词。"""
        return load_prompt_md(cls.PLANNER_TOKEN)

    @classmethod
    def writer(cls) -> str:
        """用例编写角色系统提示词。"""
        return load_prompt_md(cls.WRITER_TOKEN)

    @classmethod
    def writer_goal(cls) -> str:
        """用例编写角色目标提示词。"""
        return load_prompt_md(cls.WRITER_GOAL_TOKEN)

    @classmethod
    def verifier(cls) -> str:
        """用例验收角色系统提示词。"""
        return load_prompt_md(cls.VERIFIER_TOKEN)

    @classmethod
    def verifier_goal(cls) -> str:
        """用例验收角色目标提示词。"""
        return load_prompt_md(cls.VERIFIER_GOAL_TOKEN)


class VoiceKnowledgePrompts:
    """知识库 Omni 语音助手系统提示词。"""

    SYSTEM_PROMPT: Final[str] = (
        "你是一个中文语音助手，正在通过语音和用户直接对话。回答尽量简短、口语化，通常不超过三句话。"
    )

    @classmethod
    def system(cls) -> str:
        """返回实时语音助手的直接对话系统提示词。"""
        return cls.SYSTEM_PROMPT


def build_system_prompt() -> str:
    """兼容 realtime_vocie.knowledge：返回语音助手系统提示词。"""
    return VoiceKnowledgePrompts.system()


SYSTEM_PROMPT: Final[str] = VoiceKnowledgePrompts.SYSTEM_PROMPT

# 智能体提示词分配（正文在 config/data/prompts/）
CASE_MODULE_PLANNER_PROMPT = CaseAuthoringPrompts.planner()
CASE_WRITER_PROMPT = CaseAuthoringPrompts.writer()
CASE_WRITER_GOAL_PROMPT = CaseAuthoringPrompts.writer_goal()
CASE_VERIFIER_PROMPT = CaseAuthoringPrompts.verifier()
CASE_VERIFIER_GOAL_PROMPT = CaseAuthoringPrompts.verifier_goal()
EXECUTOR_PROMPT = UiControlPrompts.executor()
VERIFIER_PROMPT = UiControlPrompts.verifier()


# ── DeepSeek 模型目录（正式模型名 → 是否支持图片输入）──
# 已迁至 engines.agents.models.catalog：提示词模块只负责提示词，不再持有模型元数据。


__all__ = [
    "CASE_MODULE_PLANNER_PROMPT",
    "CASE_VERIFIER_GOAL_PROMPT",
    "CASE_VERIFIER_PROMPT",
    "CASE_WRITER_GOAL_PROMPT",
    "CASE_WRITER_PROMPT",
    "CHINESE_DEMAND",
    "CaseAuthoringPrompts",
    "EXECUTOR_PROMPT",
    "SYSTEM_PROMPT",
    "UiControlPrompts",
    "VERIFIER_PROMPT",
    "VoiceKnowledgePrompts",
    "build_system_prompt",
    "load_app_info_md",
    "load_prompt_md",
    "resolve_system_prompt",
    "with_app_info",
]
