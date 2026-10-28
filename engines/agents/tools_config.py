"""角色工具与技能选择。改下面的名字表即可。"""

from __future__ import annotations

import os

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from agentscope.skill import LocalSkillLoader, Skill, SkillLoaderBase
from agentscope.tool import ToolGroup, Toolkit

from .tools import build_toolkit
from .tools.tool_case_module_store import (
    ModuleStore,
    build_verifier_store_tools,
    build_writer_store_tools,
)
from .tools.tool_case_plan import build_case_plan_tools
from .tools.tool_device import device_tool_specs
from .tools.tool_img_b64 import img_b64_tool_specs
from .tools.tool_serial import serial_tool_specs
from .tools.tool_wrapper import PlatformFunctionTool

_REPO_ROOT = Path(__file__).resolve().parents[2]
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


# 执行角色常驻工具。截图、坐标核对和返回键始终交给模型。
EXECUTOR_BASIC_TOOL_NAMES = (
    "screenshot_page",
    "mark_dot",
    "press_key",
)

# 验收角色常驻工具。截图看页面，日志只走关键词检查。
VERIFIER_BASIC_TOOL_NAMES = (
    "screenshot_page",
    "check_device_log",
)

# 执行角色启用的技能目录。删掉一行即不交给模型。目录下的子目录也会扫描。
EXECUTOR_SKILLS_NAMES = [
    "engines/agents/skills/executor",
]

# 执行角色可开关组。模型用组开关一次写完全部组的最终状态。
EXECUTOR_TOOL_GROUPS = (
    ToolGroupSpec(
        name="gesture",
        description="点击滑动。按坐标或方向点击、长按、滑动、拖动。",
        instructions="看图后的点击、长按、滑动、拖动；有相对位置时用归一化坐标。",
        tool_names=("click_ratio", "tap_screen", "swipe_screen", "drag_ratio"),
    ),
    ToolGroupSpec(
        name="xpath",
        description="xpath。获取页面 xpath 元素的文本与中心坐标。",
        instructions="已有 xpath 时先取文本和坐标，再用 tap_screen 按像素坐标点击或长按。",
        tool_names=("xpath_action",),
    ),
    ToolGroupSpec(
        name="text_input",
        description="输入。向当前输入框输入文本。",
        instructions="向当前输入框输入，默认先清空。",
        tool_names=("input_text",),
    ),
    ToolGroupSpec(
        name="app",
        description="启停应用。启动或停止指定应用。",
        instructions="启动或停止前确认包名。",
        tool_names=("app_control",),
    ),
    ToolGroupSpec(
        name="platform_business",
        description="平台业务工具。查阅平台可调用工具的用途、组合与校验规则。",
        instructions="先读取技能全文，再按全文选择工具；技能本身不能当工具调用。",
        skill_dirs=tuple(EXECUTOR_SKILLS_NAMES),
    ),
)


def build_executor_toolkit(
    basic_tool_names: tuple[str, ...] | None = None,
    groups: tuple[ToolGroupSpec, ...] | None = None,
) -> Toolkit:
    """按组表组装一份新的执行角色工具包。

    Args:
        basic_tool_names: 常驻工具名。省略时用执行角色常驻表。
        groups: 可开关组。省略时用执行角色组表。

    Returns:
        新的 Toolkit。常驻工具在 basic，其余工具和技能在对应组。
    """
    basic = EXECUTOR_BASIC_TOOL_NAMES if basic_tool_names is None else basic_tool_names
    chosen = EXECUTOR_TOOL_GROUPS if groups is None else groups
    owner = _assigned_tools(basic, chosen)
    by_name = {spec.name: spec for spec in select_tools(tuple(owner))}
    tool_groups = [
        ToolGroup(
            name=group.name,
            description=group.description,
            instructions=group.instructions,
            tools=[PlatformFunctionTool(by_name[name]) for name in group.tool_names],
            skills_or_loaders=[
                LocalSkillLoader(directory=directory, scan_subdir=True)
                for directory in resolve_skill_dirs(group.skill_dirs)
            ],
        )
        for group in chosen
    ]
    return build_toolkit([by_name[name] for name in basic], tool_groups=tool_groups)


def build_verifier_toolkit() -> Toolkit:
    """组装验收角色工具包：截图与日志检查常驻，不带设备操作。"""
    return build_executor_toolkit(VERIFIER_BASIC_TOOL_NAMES, ())


def build_case_authoring_toolkit() -> Toolkit:
    """组装规划/验收角色共用的空工具包：不操作设备，也不读写文件。

    Returns:
        只含 basic 组、不含任何工具的新 Toolkit。
    """
    return build_toolkit([])


def build_case_writer_toolkit() -> Toolkit:
    """组装写用例角色的工具包：只带计划模式四件套，不操作设备。

    Returns:
        basic 组内含 ``TaskCreate`` / ``TaskGet`` / ``TaskList`` / ``TaskUpdate``。
    """
    return Toolkit(tools=build_case_plan_tools())


def build_case_module_store_tools(
    store: ModuleStore,
    module_key: str,
    *,
    read_only: bool = False,
):
    """组装 GoalPipeline 模块存储工具：编写角色可写，验收角色只读。

    Args:
        store: 本次任务共享的模块存储。
        module_key: 当前模块 KEY，工具闭包固定该值。
        read_only: 为真时只返回读取工具。

    Returns:
        可直接挂到角色 Toolkit 的 FunctionTool 列表。
    """
    if read_only:
        return build_verifier_store_tools(store, module_key)
    return build_writer_store_tools(store, module_key)


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
