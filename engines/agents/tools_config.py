"""
文件名: ➡️ tools_config.py 🏁
路径: ➡️ engines/agents/tools_config.py 🏁
模块功能：➡️ 按模块把工具集合装成 Toolkit，并在创建时激活已授予的组 🏁
Python 调试：➡️ python -m engines.agents.tools_config 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. TOOL_MODULES: device / observe / serial 三个模块，授予一个就给该集合全部工具。
2. build_toolkit_for_modules: 按模块名装 Toolkit；组可被 reset_tools 关闭，创建时由调用方激活。
3. role_modules: 从角色表的 ToolsConfig.modules 取模块名；空节表示不授静态工具。
4. activate_modules: 把已授予的组写进 Agent 状态，模型第一轮就能看见。
5. select_tools / register_skills: 按名字取规格、追加技能，仍供测试与技能注册使用。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/engines/agents/unit/test_ocr_tool.py: OCR 不进入任何静态模块
2. tests/engines/agents/unit/test_tool_img_b64.py: mark_dot 属于 observe
3. tests/engines/agents/unit/test_tool_modules.py: 模块授予、初始激活与 reset_tools 覆盖
🏁
"""

from __future__ import annotations

import os

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from agentscope.skill import LocalSkillLoader, Skill, SkillLoaderBase
from agentscope.tool import ToolGroup, Toolkit

from .tools.tool_device import device_tool_specs
from .tools.tool_img_b64 import img_b64_tool_specs
from .tools.tool_serial import serial_tool_specs
from .tools.tool_wrapper import PlatformFunctionTool, build_toolkit

_REPO_ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "DEFAULT_ROLE_MODULES",
    "TOOL_MODULES",
    "ToolGroupSpec",
    "activate_modules",
    "build_case_artifact_tools",
    "build_case_authoring_toolkit",
    "build_executor_toolkit",
    "build_toolkit_for_modules",
    "build_verifier_toolkit",
    "register_skills",
    "resolve_skill_dirs",
    "role_modules",
    "select_tools",
]
_SkillSource = str | Skill | SkillLoaderBase


@dataclass(frozen=True)
class ToolGroupSpec:
    """
    一个可开关工具组的标识、说明和成员。
    Attributes:
        name: 工具组名称
        description: 工具组描述
        instructions: 工具组使用说明
        tool_names: 工具组包含的工具名
        skill_dirs: 工具组包含的技能目录
    """

    name: str
    description: str
    instructions: str
    tool_names: tuple[str, ...] = ()
    skill_dirs: tuple[str, ...] = ()


def select_tools(names: tuple[str, ...]):
    """按名字表取出 ToolSpec，顺序与名字表一致。未知名字直接报错。

    Args:
        names: 要取出的工具名。

    Returns:
        工具规格列表，顺序与 `names` 一致。

    Raises:
        ValueError: 名字表里有未登记的工具（报错会列出可选名）。
    """
    by_name = {
        spec.name: spec
        for spec in (*device_tool_specs(), *serial_tool_specs(), *img_b64_tool_specs())
    }
    missing = [name for name in names if name not in by_name]
    if missing:
        known = ", ".join(by_name)
        raise ValueError(f"未知工具: {', '.join(missing)}；可选：{known}")
    return [by_name[name] for name in names]


def resolve_skill_dirs(names: list[str] | tuple[str, ...]) -> list[str]:
    """把技能目录收成绝对路径。相对路径按仓库根目录解析，空字符串跳过。"""
    resolved: list[str] = []
    for name in names:
        text = name.strip()
        if not text:
            continue
        path = Path(text)
        if not path.is_absolute():
            path = _REPO_ROOT / path
        resolved.append(str(path))
    return resolved


def _assigned_tools(
    basic_tool_names: tuple[str, ...],
    groups: tuple[ToolGroupSpec, ...],
) -> dict[str, str]:
    """记录每个工具名属于哪一组。同一名字出现两次则报错。

    Args:
        basic_tool_names: 常驻组（basic）的工具名。
        groups: 可开关工具组。

    Returns:
        工具名 → 所属组名的映射。

    Raises:
        ValueError: 同一工具名同时列入 basic 与某个可开关组。
    """
    owner: dict[str, str] = {}
    for name in basic_tool_names:
        if name in owner:
            raise ValueError(f"工具 {name} 同时列入 {owner[name]} 和 basic")
        owner[name] = "basic"
    for group in groups:
        for name in group.tool_names:
            if name in owner:
                raise ValueError(f"工具 {name} 同时列入 {owner[name]} 和 {group.name}")
            owner[name] = group.name
    return owner


# 三个静态模块。授予模块名即给该集合全部工具，配置里不写单个函数名。
# device 只含写操作；截图与坐标核对在 observe，避免验收角色一授权就拿到点击。
_DEVICE_TOOLS = (
    "click_ratio",
    "tap_screen",
    "xpath_action",
    "swipe_screen",
    "drag_ratio",
    "input_text",
    "press_key",
    "app_control",
)
_OBSERVE_TOOLS = (
    "screenshot_page",
    "mark_dot",
    "check_device_log",
)
_SERIAL_TOOLS = ("check_device_log",)

TOOL_MODULES: dict[str, ToolGroupSpec] = {
    "device": ToolGroupSpec(
        name="device",
        description="设备操作。点击、滑动、输入、按键、启停应用、按文案取坐标。",
        instructions="看图核对后再点击；有文案时先取坐标，再按标记点操作。",
        tool_names=_DEVICE_TOOLS,
    ),
    "observe": ToolGroupSpec(
        name="observe",
        description="只读观察。截图、坐标核对、日志关键词检查。",
        instructions="只看不操作；截图与日志结果用来核对，不产生手势。",
        tool_names=_OBSERVE_TOOLS,
    ),
    "serial": ToolGroupSpec(
        name="serial",
        description="串口日志。在当前抓取文件里检查关键词。",
        instructions="只查已抓取的日志，不启动采集，也不操作设备。",
        tool_names=_SERIAL_TOOLS,
    ),
}

# 角色未写 ToolsConfig.modules 时的默认。空元组表示不授静态工具。
DEFAULT_ROLE_MODULES = {
    "UI_EXECUTOR_ROLE_CONFIG": ("device", "observe"),
    "UI_VERIFIER_ROLE_CONFIG": ("observe",),
}


def role_modules(roles: dict, role_key: str) -> tuple[str, ...]:
    """从角色表读取该角色授予的模块名。

    Args:
        roles: 整张角色表。
        role_key: 角色键。

    Returns:
        模块名。节里没写 modules 时用默认；默认也没有则为空。

    Raises:
        ValueError: modules 不是字符串列表，或含未知模块名。
    """
    section = roles.get(role_key) if isinstance(roles, dict) else None
    tools = section.get("ToolsConfig") if isinstance(section, dict) else None
    raw = tools.get("modules") if isinstance(tools, dict) else None
    if raw is None:
        return DEFAULT_ROLE_MODULES.get(role_key, ())
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"{role_key}.ToolsConfig.modules 必须是模块名列表")
    unknown = [item for item in raw if item not in TOOL_MODULES]
    if unknown:
        known = ", ".join(sorted(TOOL_MODULES))
        raise ValueError(f"{role_key} 未知工具模块：{', '.join(unknown)}；可选：{known}")
    return tuple(raw)


def build_toolkit_for_modules(modules: tuple[str, ...] | list[str]) -> Toolkit:
    """按模块名装一份新的 Toolkit。

    每个模块是一个可开关组。basic 留空，因此框架会注册 reset_tools。
    组在创建时是未激活的，调用方必须再调用 activate_modules。

    Args:
        modules: 模块名，顺序即组顺序。

    Returns:
        新的 Toolkit。

    Raises:
        ValueError: 模块名未知，或两个模块登记了同一个工具名。
    """
    unknown = [name for name in modules if name not in TOOL_MODULES]
    if unknown:
        known = ", ".join(sorted(TOOL_MODULES))
        raise ValueError(f"未知工具模块：{', '.join(unknown)}；可选：{known}")
    chosen = tuple(TOOL_MODULES[name] for name in modules)
    owner = _assigned_tools((), chosen)
    by_name = {spec.name: spec for spec in select_tools(tuple(owner))}
    groups = [
        ToolGroup(
            name=group.name,
            description=group.description,
            instructions=group.instructions,
            tools=[PlatformFunctionTool(by_name[name]) for name in group.tool_names],
        )
        for group in chosen
    ]
    return build_toolkit([], tool_groups=groups)


def activate_modules(agent, modules: tuple[str, ...] | list[str]) -> None:
    """把已授予的工具组写进 Agent 状态，使模型第一轮就能看见。

    之后模型仍可调用 reset_tools 覆盖。没授予的模块不会出现在工具包里。

    Args:
        agent: 已创建的智能体，需有 state.tool_context。
        modules: 要激活的模块名，必须已注册在该智能体的工具包中。
    """
    groups = agent.state.tool_context.activated_groups
    groups.clear()
    groups.extend(modules)


def build_executor_toolkit() -> Toolkit:
    """执行角色工具包：设备操作 + 只读观察，两组都可被 reset_tools 关闭。

    Returns:
        含 device 与 observe 两组的新 Toolkit。组尚未激活。
    """
    return build_toolkit_for_modules(DEFAULT_ROLE_MODULES["UI_EXECUTOR_ROLE_CONFIG"])


def build_verifier_toolkit() -> Toolkit:
    """验收角色工具包：只有只读观察，不含设备操作。

    Returns:
        只含 observe 组的新 Toolkit。组尚未激活。
    """
    return build_toolkit_for_modules(DEFAULT_ROLE_MODULES["UI_VERIFIER_ROLE_CONFIG"])


def build_case_authoring_toolkit() -> Toolkit:
    """组装用例编写/验收角色共用的空工具包：不操作设备，也不读写文件。

    产物工具由流水线在运行时按任务注入（见 `build_case_artifact_tools`）。

    Returns:
        只含 basic 组、不含任何工具的新 Toolkit。
    """
    return build_toolkit([])


def build_case_artifact_tools(store, *, read_only: bool = False, requirement_text: str = ""):
    """组装三段式产物的增量工具：编写角色可写，验收角色只读。

    Args:
        store: 本次任务共享的产物存储。
        read_only: 为真时只返回读取工具。
        requirement_text: 需求正文；验收角色用它开启事实预检。

    Returns:
        可直接挂到角色 Toolkit 的 FunctionTool 列表。
    """
    # 延迟导入：产物工具依赖 workflow 包，模块级导入会与 workflow.__init__ 形成环
    from .tools.tool_case_artifact import build_artifact_store_tools

    return build_artifact_store_tools(
        store,
        read_only=read_only,
        requirement_text=requirement_text,
    )


# ── 技能注册（工具包 + 技能来源） ──
def register_skills(
    toolkit: Toolkit,
    skills: Sequence[_SkillSource],
    *,
    scan_subdir: bool = True,
    group_name: str | None = None,
) -> None:
    """把 skill 来源追加到工具包的指定组。

    Args:
        toolkit: 目标工具包。
        skills: 目录路径、Skill 对象或 SkillLoaderBase。
        scan_subdir: 目录路径是否扫描子目录。
        group_name: 目标组标识。省略时追加到 basic。

    Returns:
        None。同一目录已在工具包任一组时跳过。组不存在时抛出 ValueError。
    """
    group = _basic_tool_group(toolkit) if group_name is None else _tool_group(toolkit, group_name)
    seen: set[str] = set()
    for existing in toolkit.tool_groups:
        for item in existing.skills_or_loaders:
            seen.add(_source_dir(item))
    seen.discard("")
    for source in _skill_sources(skills, scan_subdir=scan_subdir):
        directory = _source_dir(source)
        if directory and directory in seen:
            continue
        if directory:
            seen.add(directory)
        group.skills_or_loaders.append(source)


def _basic_tool_group(toolkit: Toolkit):
    """返回工具包里始终启用的 basic 组。"""
    return _tool_group(toolkit, "basic")


def _tool_group(toolkit: Toolkit, name: str):
    """按标识返回工具组。

    Args:
        toolkit: 目标工具包。
        name: 组标识。

    Returns:
        同名工具组。

    Raises:
        RuntimeError: 工具包缺少 basic 组。
        ValueError: 工具包中没有该组。
    """
    for group in toolkit.tool_groups:
        if group.name == name:
            return group
    if name == "basic":
        raise RuntimeError("工具包缺少 basic 组")
    raise ValueError(f"工具包中不存在工具组: {name}")


def _skill_sources(
    skills: Sequence[_SkillSource],
    *,
    scan_subdir: bool,
) -> list[Skill | SkillLoaderBase]:
    """把路径、Skill、加载器收成 Toolkit 能挂上的来源。

    Args:
        skills: skill 来源，可以是目录路径、`Skill` 或 `SkillLoader`。
        scan_subdir: 目录来源是否递归扫描子目录。

    Returns:
        可直接挂到 Toolkit 的来源列表。

    Raises:
        TypeError: 来源既不是目录路径，也不是 `Skill` / `SkillLoaderBase`。
    """
    sources: list[Skill | SkillLoaderBase] = []
    for item in skills:
        if isinstance(item, str):
            directory = item.strip()
            if not directory:
                continue
            sources.append(
                LocalSkillLoader(
                    directory=resolve_skill_dirs([directory])[0],
                    scan_subdir=scan_subdir,
                )
            )
            continue
        if isinstance(item, (Skill, SkillLoaderBase)):
            sources.append(item)
            continue
        raise TypeError(
            f"skill 来源必须是目录路径、Skill 或 SkillLoader，收到 {type(item).__name__}"
        )
    return sources


def _source_dir(source) -> str:
    """取出加载器扫描目录或 Skill 所在目录，用于去重。"""
    directory = getattr(source, "directory", None) or getattr(source, "dir", None)
    if not directory:
        return ""
    return os.path.abspath(directory)
