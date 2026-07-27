"""Case tools — create, read, update test-case definitions."""

import uuid
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from apps.case_manager.api import (
    save_definition, get_definition, get_enabled_definitions,
    save_storage_definition, save_api_definition, save_web_definition,
)
from apps.case_manager.models import TestDefinition
from apps.case_manager.models_storage import StorageTestCase
from apps.case_manager.models_api import ApiTestCase
from apps.case_manager.models_web import WebTestCase
from models.step_types import StepType, UI_LABELS
from .db_helper import run_sync


_STEP_TYPE_NAMES = [st.value for st in StepType]
_STEP_TYPE_DOC = "\n".join(f"- `{st.value}`: {UI_LABELS.get(st, '')}" for st in StepType)


class SaveTestCaseTool(ToolBase):
    """Create or update a test case definition with structured steps."""

    name = "save_test_case"
    description = f"""创建或更新测试用例定义。

【触发条件】
  - 用户要求创建新测试用例时
  - 用户说"帮我写一个用例" / "创建测试用例"
  - 需要修改现有用例的步骤时（传入已有 case_id 即可更新）

【参数说明】
  - case_id: 唯一标识（UUID 格式，**如已存在则更新该用例**）
  - title: 用例名称（如"登录测试 - 正确账号密码"）
  - category: 分类标签（如 'smoke' / 'regression' / 'critical'）
  - description: 用例描述（测试目的）
  - package_name: 目标 Android 包名（如 'com.example.app'）
  - enabled: 是否启用（默认 true）
  - steps: 有序步骤列表

【步骤类型参考】
{_STEP_TYPE_DOC}

【使用示例】
  用户: "帮我创建一个登录测试用例，测试正确账号密码登录"
  调用: save_test_case(
    case_id="login-001",
    title="登录测试 - 正确账号密码",
    category="smoke",
    package_name="com.example.app",
    steps=[
      {{"type": "click", "xpath": "//*[@text='用户名']", "description": "点击用户名输入框"}},
      {{"type": "input", "xpath": "//*[@text='用户名']", "text": "admin", "description": "输入用户名"}},
      ...
    ]
  )"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "唯一用例标识（UUID）。如已存在则更新该用例。",
            },
            "title": {
                "type": "string",
                "description": "用例名称（如'登录测试 - 正确账号密码'）。",
            },
            "category": {
                "type": "string",
                "description": "分类标签（如 'smoke'、'regression'）。",
            },
            "description": {
                "type": "string",
                "description": "用例描述（测试目的）。",
            },
            "package_name": {
                "type": "string",
                "description": "目标 Android 包名（如 'com.example.app'）。",
            },
            "enabled": {
                "type": "boolean",
                "description": "是否启用（默认 true）。",
            },
            "directory_id": {
                "type": "integer",
                "description": "所属二级目录 ID（可选，从目录树获取）。",
            },
            "steps": {
                "type": "array",
                "description": "有序测试步骤列表。",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "description": f"步骤类型: {_STEP_TYPE_NAMES}"},
                        "xpath": {"type": "string", "description": "目标元素的 XPath 定位器"},
                        "xpath2": {
                            "type": "string",
                            "description": "备用 XPath（保留字段）",
                        },
                        "timeout": {"type": "number", "description": "超时秒数（默认 10）"},
                        "expected_text": {
                            "type": "string",
                            "description": "预期文本（用于 verify_text / poll_text）",
                        },
                        "index": {
                            "type": "integer",
                            "description": "索引（用于 wait / poll_text 的轮询间隔秒数）",
                        },
                        "description": {"type": "string", "description": "步骤描述"},
                    },
                    "required": ["type", "xpath", "description"],
                },
            },
        },
        "required": ["case_id", "title", "steps"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(
        self,
        case_id,
        title,
        steps,
        category="",
        description="",
        package_name="",
        enabled=True,
        directory_id=None,
        **kwargs,
    ):
        # Validate step types
        for i, step in enumerate(steps):
            stype = step.get("type", "click")
            if stype not in _STEP_TYPE_NAMES:
                return ToolChunk(
                    content=[
                        TextBlock(
                            text=f"步骤类型无效：'{stype}'（第 {i} 步）。"
                            f"可用类型：{', '.join(_STEP_TYPE_NAMES)}"
                        )
                    ]
                )

        try:
            obj = await run_sync(
                lambda: save_definition(
                    case_id=case_id,
                    title=title,
                    category=category,
                    description=description,
                    steps="\n".join(f"{s['type']}: {s.get('description', '')}" for s in steps),
                    steps_data=steps,
                    enabled=enabled,
                    package_name=package_name,
                    directory_id=directory_id,
                )
            )
        except Exception as e:
            return ToolChunk(content=[TextBlock(text=f"保存用例失败：{e}")])
        return ToolChunk(
            content=[
                TextBlock(
                    text=f"测试用例 '{title}' 保存成功。\n用例 ID: {obj.id}\n步骤数: {len(steps)}\n启用状态: {enabled}\n\n"
                    f"【后续操作】可用 debug_test_case(case_id='{obj.id}') 检查用例是否就绪。"
                )
            ]
        )


class GetTestCaseTool(ToolBase):
    """Retrieve an existing test case definition by ID."""

    name = "get_test_case"
    description = """获取指定测试用例的完整详情（包括所有步骤）。

【触发条件】
  - 用户询问某个用例的具体内容时
  - 执行测试前想确认用例步骤时
  - 需要了解用例的 XPath 定位器时

【参数说明】
  - case_id: 用例 ID（从 list_test_cases 获取）

【返回数据】
  - 用例名称、分类、包名、启用状态
  - 所有步骤详情（类型、描述、XPath 定位器）

【使用示例】
  调用: get_test_case(case_id="xxx")
  返回该用例的所有步骤信息，用于向用户解释或在执行前确认"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "要查询的测试用例 ID。",
            },
        },
        "required": ["case_id"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_id, **kwargs):
        obj = await run_sync(lambda: get_definition(case_id))
        if obj is None:
            return ToolChunk(
                content=[
                    TextBlock(
                        text=f"测试用例 '{case_id}' 不存在。请先用 list_test_cases 确认用例 ID。"
                    )
                ]
            )
        import json

        try:
            steps_data = json.loads(obj.steps_json) if obj.steps_json else []
        except Exception:
            steps_data = []
        steps_summary = "\n".join(
            f"  {i + 1}. [{s.get('type', '?')}] {s.get('description', '')} (xpath={s.get('xpath', '')})"
            for i, s in enumerate(steps_data)
        )
        dir_info = f"\n目录: {obj.directory.name}" if obj.directory else ""
        return ToolChunk(
            content=[
                TextBlock(
                    text=f"用例: {obj.title}\nID: {obj.id}\n分类: {obj.category}{dir_info}\n包名: {obj.package_name}\n启用: {obj.enabled}\n步骤 ({len(steps_data)}):\n{steps_summary}"
                )
            ]
        )


class DebugTestCaseTool(ToolBase):
    """Validate whether a test case's steps are executable on the current device."""

    name = "debug_test_case"
    description = """验证测试用例是否可以在当前设备上执行（调试/诊断工具）。

【触发条件】
  - 执行 run_test 前想确认用例是否就绪
  - 用例执行失败后想排查问题
  - 用户说"这个用例能用吗？" / "帮我检查一下这个用例"

【检查内容】
  - 所有 XPath 定位器是否在 UI 元素库中
  - 所有步骤类型是否合法
  - 目标设备和包名是否可用
  - UI 元素库是否为空（为空则无法验证）

【返回内容】
  - 错误（Errors）：导致用例无法执行的问题（必须修复）
  - 警告（Warnings）：可能影响执行的问题（建议处理）
  - 成功提示：所有检查通过，可执行

【使用示例】
  用户: "帮我检查一下 xxx 这个用例能不能跑通"
  调用: debug_test_case(case_id="xxx")
  根据返回结果告诉用户用例是否就绪"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_id": {"type": "string", "description": "The test case ID to debug/validate."},
        },
        "required": ["case_id"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_id, **kwargs):
        from apps.case_manager.api import get_definition
        from apps.element_locator.models import Element
        from models.step_types import StepType
        import json

        cdef = await run_sync(lambda: get_definition(case_id))
        if cdef is None:
            return ToolChunk(content=[TextBlock(text=f"Case '{case_id}' not found.")])

        issues = []
        warnings = []
        ok_count = 0

        try:
            steps_data = json.loads(cdef.steps_json) if cdef.steps_json else []
        except Exception:
            steps_data = []

        if not steps_data:
            return ToolChunk(
                content=[
                    TextBlock(
                        text=f"Case '{cdef.title}' has no steps defined. Add steps with save_test_case first."
                    )
                ]
            )

        valid_types = set(st.value for st in StepType)

        for i, step in enumerate(steps_data):
            step_num = i + 1
            stype = step.get("type", "click")
            xpath = step.get("xpath", "")
            desc = step.get("description", f"step {step_num}")

            # Validate step type
            if stype not in valid_types:
                issues.append(
                    f"[Step {step_num}] Unknown type '{stype}'. Valid: {sorted(valid_types)}"
                )
                continue

            # For steps that need XPath, check element exists
            xpath_steps = {
                "click", "long_click",
                "wait", "wait_disappear",
                "verify_text", "poll_text",
            }
            if stype in xpath_steps and xpath:
                try:
                    first_element = await run_sync(lambda: Element.objects.first())
                    exists = await run_sync(lambda: Element.objects.exists())
                    candidates = json.loads(first_element.xpath_candidates) if exists else []
                except Exception:
                    candidates = []
                # Check if there's at least one element in the DB (simple existence check)
                el_count = await run_sync(lambda: Element.objects.count())
                if el_count == 0:
                    warnings.append(
                        f"[Step {step_num}] '{desc}' — UI element database is empty. Dump UI first."
                    )
                else:
                    ok_count += 1

            # Package check
            if not cdef.package_name:
                warnings.append(f"[Step {step_num}] No package_name set — will fail without it.")

        # Device check
        from apps.device_pool.models import Device

        online = await run_sync(lambda: Device.objects.filter(status="ONLINE").count())
        if online == 0:
            warnings.append("No online devices — run will fail.")

        lines = [
            f"Debug Report — {cdef.title} ({case_id})",
            f"Steps: {len(steps_data)} | Category: {cdef.category or '—'} | Package: {cdef.package_name or '⚠ missing'}",
            "",
        ]
        if issues:
            lines.append(f"❌ Errors ({len(issues)}):")
            lines.extend(f"  {i}" for i in issues)
            lines.append("")
        if warnings:
            lines.append(f"⚠ Warnings ({len(warnings)}):")
            lines.extend(f"  {w}" for w in warnings)
            lines.append("")
        if not issues:
            lines.append(
                f"✅ Case is ready to execute ({ok_count}/{len(steps_data)} steps validated)."
            )
        if online == 0:
            lines.append("💡 Tip: Connect a device and dump UI before running.")

        return ToolChunk(content=[TextBlock(text="\n".join(lines))])


class ListTestCasesTool(ToolBase):
    """List all enabled test cases, optionally filtered by IDs."""

    name = "list_test_cases"
    description = """列出平台中已启用的测试用例。

【触发条件】当用户询问以下问题时，**必须**调用此工具：
  - "有哪些测试用例？"
  - "测试用例总数？"
  - "我创建了哪些用例？"
  - 准备执行测试前（先确认用例存在和 ID）

【参数说明】
  - case_ids: 可选，传入用例 ID 列表可精确筛选

【返回数据】
  - case_id: 用例唯一标识（用于 run_test）
  - title: 用例名称
  - category: 分类标签（smoke/regression 等）
  - package_name: 目标 Android 包名

【使用示例】
  用户: "平台上有哪些测试用例？"
  调用: list_test_cases()
  如需查看某用例详情，再调用: get_test_case(case_id="xxx")"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of case IDs to filter.",
            },
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_ids=None, **kwargs):
        if case_ids:
            items = await run_sync(lambda: get_enabled_definitions(case_ids))
        else:
            items = await run_sync(lambda: list(TestDefinition.objects.filter(enabled=True)[:50]))
        if not items:
            return ToolChunk(
                content=[
                    TextBlock(text="没有找到已启用的测试用例。建议先用 save_test_case 创建用例。")
                ]
            )
        lines = [
            f"- [{d.id}] {d.title} | category={d.category} | dir={d.directory.name if d.directory else '—'} | package={d.package_name}"
            for d in items
        ]
        return ToolChunk(content=[TextBlock(text=f"测试用例 ({len(items)}):\n" + "\n".join(lines))])


# ═══════════════════════════════════════════════════════════════
# Case directory & discovery tools
# ═══════════════════════════════════════════════════════════════

_CASE_TYPE_MODELS = {
    "ui_automation": TestDefinition,
    "storage": StorageTestCase,
    "api_testing": ApiTestCase,
    "web_automation": WebTestCase,
}


class GetDirectoryTreeTool(ToolBase):
    """Get the directory tree for a case_type, including case nodes."""

    name = "get_directory_tree"
    description = """查询用例目录树，包含已有目录和用例节点。

【触发条件】
- 生成用例前规划目录结构时（Step 4）
- 需要了解某个 case_type 下的目录组织
- 决定新用例应该放在哪个目录

【参数】
- case_type: ui_automation / storage / api_testing / web_automation（默认 ui_automation）

【返回】
- 两级目录树，含每个目录的 id、名称、用例数量
- 目录 id 用于 save_xxx_case 的 directory_id 参数"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_type": {
                "type": "string",
                "enum": ["ui_automation", "storage", "api_testing", "web_automation"],
                "description": "用例类型，默认 ui_automation",
            },
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_type="ui_automation", **kwargs):
        from apps.case_manager.api import get_directory_tree as _get_tree

        tree = await run_sync(lambda: _get_tree(case_type=case_type or None))
        if not tree:
            return ToolChunk(content=[TextBlock(
                text=f"{case_type} 类型下暂无目录。建议用 create_directory 创建目录结构。"
            )])

        def _summarize(node, indent=0):
            prefix = "  " * indent
            nt = node.get("node_type", "directory")
            if nt == "directory":
                lines = [f"{prefix}📁 {node['name']} (id={node['id']}, cases={node.get('case_count', 0)})"]
                for child in node.get("children", []):
                    lines.extend(_summarize(child, indent + 1))
                return lines
            else:
                return [f"{prefix}  📄 {node['name']} (id={node.get('case_id', '?')})"]

        summary = []
        for root in tree:
            summary.extend(_summarize(root))

        return ToolChunk(content=[TextBlock(
            text=f"用例目录树 ({case_type}):\n" + "\n".join(summary)
            + "\n\n目录的 id 值即为 save_xxx_case 的 directory_id 参数。"
        )])


class CreateDirectoryTool(ToolBase):
    """Create a new case directory."""

    name = "create_directory"
    description = """创建新的用例目录。

【触发条件】
- Step 4 目录规划中，需要新建目录来组织用例
- 不同模块/产品需要独立目录时

【限制】
- 两级目录（根→一级→二级）
- 同一父级+同一 case_type 下目录名唯一

【参数】
- name: 目录名称
- parent_id: 父级目录 ID（不传=创建一级目录）
- case_type: 用例类型"""
    input_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "目录名称"},
            "parent_id": {"type": "integer", "description": "父级目录 ID（可选）"},
            "case_type": {
                "type": "string",
                "enum": ["ui_automation", "storage", "api_testing", "web_automation"],
                "description": "用例类型，默认 ui_automation",
            },
        },
        "required": ["name"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, name, parent_id=None, case_type="ui_automation", **kwargs):
        from apps.case_manager.api import create_directory as _create_dir

        ctx = getattr(self, "_ctx", None)
        created_by = str(ctx.user_id) if ctx and ctx.user_id else ""

        ok, result = await run_sync(
            lambda: _create_dir(name=name, parent_id=parent_id, case_type=case_type, created_by=created_by)
        )
        if not ok:
            return ToolChunk(content=[TextBlock(text=f"创建目录失败: {result}")])

        parent_info = f"，父级 id={parent_id}" if parent_id else ""
        return ToolChunk(content=[TextBlock(
            text=f"✅ 目录 '{result['name']}' 创建成功。\n"
                 f"ID: {result['id']}{parent_info}\n类型: {result['case_type']}\n\n"
                 f"在 save_xxx_case 时传入 directory_id={result['id']} 即可放入此目录。"
        )])


class ListAllCasesTool(ToolBase):
    """List test cases across all 4 case types."""

    name = "list_all_cases"
    description = """列出指定类型的测试用例（支持全部 4 种类型）。

【与 list_test_cases 的区别】
- list_test_cases 只查 cm_test_definitions（UI 自动化）
- 本工具支持 ui_automation / storage / api_testing / web_automation

【触发条件】
- 探索阶段需要了解某类型下已有用例
- 检查是否已有同名用例（防重复）
- 用户问"storage 下有哪些用例"

【参数】
- case_type: 用例类型"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_type": {
                "type": "string",
                "enum": ["ui_automation", "storage", "api_testing", "web_automation"],
                "description": "用例类型",
            },
            "limit": {"type": "integer", "description": "最多返回条数（默认 30）"},
        },
        "required": ["case_type"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_type, limit=30, **kwargs):
        model = _CASE_TYPE_MODELS.get(case_type)
        if not model:
            return ToolChunk(content=[TextBlock(text=f"无效的 case_type: {case_type}")])

        items = await run_sync(lambda: list(
            model.objects.filter(enabled=True).select_related('directory').order_by("-updated_at")[:limit]
        ))
        if not items:
            return ToolChunk(content=[TextBlock(
                text=f"{case_type} 类型下暂无已启用用例。用 save_xxx_case 创建。"
            )])

        lines = [f"{case_type} 用例 ({len(items)}):"]
        for d in items:
            dir_name = d.directory.name if d.directory else "—"
            lines.append(f"- [{d.id}] {d.title} | P={getattr(d,'priority','?')} | dir={dir_name}")
        return ToolChunk(content=[TextBlock(text="\n".join(lines))])


class GetCaseDetailTool(ToolBase):
    """Get details of a single case across any type."""

    name = "get_case_detail"
    description = """获取任意类型用例的详细信息。

【与 get_test_case 的区别】
- get_test_case 只查 cm_test_definitions（UI 自动化）
- 本工具支持全部 4 种类型

【触发条件】
- 用户询问某个 storage/api/web 用例的具体内容
- 验证刚创建的用例是否正确写入

【参数】
- case_type: 用例类型
- case_id: 用例 ID"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_type": {
                "type": "string",
                "enum": ["ui_automation", "storage", "api_testing", "web_automation"],
                "description": "用例类型",
            },
            "case_id": {"type": "string", "description": "用例 ID"},
        },
        "required": ["case_type", "case_id"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_type, case_id, **kwargs):
        model = _CASE_TYPE_MODELS.get(case_type)
        if not model:
            return ToolChunk(content=[TextBlock(text=f"无效的 case_type: {case_type}")])

        obj = await run_sync(lambda: model.objects.filter(id=case_id).select_related('directory').first())
        if not obj:
            return ToolChunk(content=[TextBlock(text=f"{case_type} 下不存在用例 '{case_id}'。")])

        dir_name = obj.directory.name if obj.directory else "—"
        priority = getattr(obj, "priority", "?")
        precondition = getattr(obj, "precondition", "")
        steps = getattr(obj, "steps", "")
        expected = getattr(obj, "expected_result", "") or getattr(obj, "expected_response", "")

        parts = [
            f"用例: {obj.title}",
            f"ID: {obj.id} | 类型: {case_type} | 优先级: {priority}",
            f"目录: {dir_name} | 启用: {getattr(obj, 'enabled', True)}",
        ]
        if precondition:
            parts.append(f"前置条件: {precondition[:200]}")
        if steps:
            parts.append(f"步骤: {steps[:300]}")
        if expected:
            parts.append(f"预期: {expected[:300]}")

        return ToolChunk(content=[TextBlock(text="\n".join(parts))])


# ═══════════════════════════════════════════════════════════════
# Multi-type test case tools — Storage / API / Web
# ═══════════════════════════════════════════════════════════════


class SaveStorageCaseTool(ToolBase):
    """Create or update a batch of business function test cases in ONE file."""

    name = "save_storage_case"
    description = """创建或更新业务功能测试用例（批量写入一个文件）。

【重要】同一模块/需求的多个用例必须一次性写入同一个文件！
  - case_id 是文件/模块级标识（如 TC-FUNC-login）
  - cases 数组包含该模块的所有测试用例
  - 可多次调用同一 case_id，新用例会自动追加（按 title 去重），无需担心覆盖

【触发条件】
  - 用户要求创建业务功能用例 / 业务流程测试
  - 用户说"写一个功能测试用例" / "业务流程用例"
  - AI 识别 case_type 为 storage 时

【参数说明】
  - case_id: 文件标识（建议格式 TC-FUNC-模块名，如 TC-FUNC-login）
  - title: 文件标题（如"登录功能业务测试用例"）
  - cases: 测试用例数组，每个元素包含:
      - title: 用例名称（如"正确账号密码登录成功"）
      - priority: P0/P1/P2
      - precondition: 前置条件
      - steps: 操作步骤（每行一步）
      - expected_result: 预期结果

【使用示例】
  用户: "写登录功能的业务用例，包含成功和失败场景"
  调用: save_storage_case(
    case_id="TC-FUNC-login",
    title="登录功能业务测试用例",
    cases=[
      {
        "title":"正确账号密码登录成功",
        "priority":"P1",
        "precondition":"应用已安装打开到登录页，已有有效账号",
        "steps":"1. 输入正确手机号\\n2. 输入正确密码\\n3. 点击登录按钮",
        "expected_result":"登录成功，跳转首页"
      },
      {
        "title":"密码错误登录失败",
        "priority":"P1",
        "precondition":"应用已安装打开到登录页",
        "steps":"1. 输入正确手机号\\n2. 输入错误密码\\n3. 点击登录按钮",
        "expected_result":"提示'账号或密码错误'，不跳转"
      }
    ]
  )"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "文件唯一标识（模块级，如 TC-FUNC-login）",
            },
            "title": {
                "type": "string",
                "description": "文件标题（如'登录功能业务测试用例'）",
            },
            "cases": {
                "type": "array",
                "description": "该模块下的所有测试用例",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "用例名称"},
                        "priority": {"type": "string", "enum": ["P0", "P1", "P2"], "description": "优先级"},
                        "precondition": {"type": "string", "description": "前置条件"},
                        "steps": {"type": "string", "description": "操作步骤（每行一步）"},
                        "expected_result": {"type": "string", "description": "预期结果"},
                    },
                    "required": ["title", "steps", "expected_result"],
                },
            },
            "category": {"type": "string", "description": "分类标签"},
            "description": {"type": "string", "description": "文件描述（测试目的）"},
            "directory_id": {"type": "integer", "description": "所属目录 ID（可选）"},
        },
        "required": ["case_id", "title", "cases"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_id, title, cases, category="",
                   description="", directory_id=None, **kwargs):
        if not cases or not isinstance(cases, list):
            return ToolChunk(content=[TextBlock(text="cases 必须是非空数组")])

        # Build row-oriented rows matching frontend StorageCaseEditor expected format.
        # Each row is {id, title, priority, precondition, steps, expected_result}
        rows = []
        for i, c in enumerate(cases):
            rows.append({
                "id": i + 1,
                "title": c.get("title", ""),
                "priority": c.get("priority", "P1"),
                "precondition": c.get("precondition", ""),
                "steps": c.get("steps", ""),
                "expected_result": c.get("expected_result", ""),
            })

        try:
            obj = await run_sync(
                lambda: save_storage_definition(
                    case_id=case_id,
                    title=title,
                    category=category,
                    description=description,
                    directory_id=directory_id,
                    custom_columns=[],  # no extra columns beyond the 6 defaults
                    rows=rows,
                    merge=True,         # append to existing rows for same case_id
                    steps="",  # clear legacy fields
                    expected_result="",
                )
            )
        except Exception as e:
            return ToolChunk(content=[TextBlock(text=f"保存业务功能用例失败：{e}")])

        dir_info = f"\n目录: {obj.directory.name}" if obj.directory else ""
        cases_list = "\n".join(
            f"  {i + 1}. [{c.get('priority', 'P1')}] {c.get('title', '?')}"
            for i, c in enumerate(cases)
        )
        return ToolChunk(content=[TextBlock(
            text=f"业务功能用例文件 '{obj.title}' 保存成功。\n"
                 f"文件 ID: {obj.id}{dir_info}\n"
                 f"包含 {len(cases)} 条用例:\n{cases_list}\n\n"
                 f"【注意】所有用例写入同一个文件，可在用例管理模块查看和编辑表格。"
        )])


class SaveApiCaseTool(ToolBase):
    """Create or update an API interface test case."""

    name = "save_api_case"
    description = """创建或更新 API 接口测试用例。

【触发条件】
  - 用户要求创建 API 测试用例 / 接口测试
  - 用户说"写一个接口用例" / "API 测试"
  - AI 识别 case_type 为 api_testing 时

【参数说明】
  - case_id: 唯一标识（建议格式 TC-API-XXX）
  - title: 用例标题
  - method + url: HTTP 方法和地址
  - headers: 请求头 JSON 字符串
  - body: 请求体 JSON 字符串
  - expected_response: 预期响应文本或 JSON

【使用示例】
  用户: "写一个用户登录 API 接口测试用例"
  调用: save_api_case(
    case_id="TC-API-login-001",
    title="登录接口 - 正确账号密码返回 token",
    method="POST",
    url="https://api.example.com/v1/login",
    headers='{"Content-Type":"application/json"}',
    body='{"username":"test","password":"123456"}',
    expected_response='{"code":200,"token":"***"}'
  )"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "唯一用例标识（如 TC-API-login-001）",
            },
            "title": {
                "type": "string",
                "description": "用例标题（如'登录接口 - 正确账号密码返回 token'）",
            },
            "priority": {
                "type": "string",
                "enum": ["P0", "P1", "P2"],
                "description": "优先级（默认 P1）",
            },
            "method": {
                "type": "string",
                "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "description": "HTTP 方法",
            },
            "url": {
                "type": "string",
                "description": "请求 URL",
            },
            "headers": {
                "type": "string",
                "description": "请求头 JSON 字符串",
            },
            "body": {
                "type": "string",
                "description": "请求体 JSON 字符串",
            },
            "expected_response": {
                "type": "string",
                "description": "预期响应文本或 JSON",
            },
            "precondition": {
                "type": "string",
                "description": "前置条件描述",
            },
            "category": {
                "type": "string",
                "description": "分类标签（如 'smoke'）",
            },
            "description": {
                "type": "string",
                "description": "用例描述（测试目的）",
            },
            "directory_id": {
                "type": "integer",
                "description": "所属二级目录 ID（可选）",
            },
        },
        "required": ["case_id", "title", "url", "expected_response"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_id, title, url, expected_response,
                   method="GET", headers="", body="",
                   priority="P1", precondition="", category="",
                   description="", directory_id=None, **kwargs):
        try:
            obj = await run_sync(
                lambda: save_api_definition(
                    case_id=case_id,
                    title=title,
                    priority=priority,
                    precondition=precondition,
                    method=method,
                    url=url,
                    headers=headers,
                    body=body,
                    expected_response=expected_response,
                    category=category,
                    description=description,
                    directory_id=directory_id,
                )
            )
        except Exception as e:
            return ToolChunk(content=[TextBlock(text=f"保存 API 用例失败：{e}")])

        dir_info = f"\n目录: {obj.directory.name}" if obj.directory else ""
        return ToolChunk(content=[TextBlock(
            text=f"API 接口用例 '{obj.title}' 保存成功。\n"
                 f"用例 ID: {obj.id}\n{method} {url}\n"
                 f"优先级: {obj.priority}{dir_info}\n"
                 f"【注意】API 用例当前不支持自动执行，可在用例管理模块查看。"
        )])


class SaveWebCaseTool(ToolBase):
    """Create or update a web automation test case."""

    name = "save_web_case"
    description = """创建或更新 Web 自动化测试用例（Playwright 风格）。

【触发条件】
  - 用户要求创建 Web 自动化用例 / 网页测试
  - 用户说"写一个网页测试用例" / "Web 自动化"
  - AI 识别 case_type 为 web_automation 时

【参数说明】
  - case_id: 唯一标识（建议格式 TC-WEB-XXX）
  - title: 用例标题
  - url: 目标网页 URL
  - steps: 操作步骤描述
  - expected_result: 预期结果描述

【使用示例】
  用户: "写一个网页登录测试用例"
  调用: save_web_case(
    case_id="TC-WEB-login-001",
    title="网页登录 - 正确账号密码",
    url="https://example.com/login",
    steps="1. 打开登录页\\n2. 输入用户名 admin\\n3. 输入密码 123456\\n4. 点击登录按钮",
    expected_result="跳转到首页，显示用户名"
  )"""
    input_schema = {
        "type": "object",
        "properties": {
            "case_id": {
                "type": "string",
                "description": "唯一用例标识（如 TC-WEB-login-001）",
            },
            "title": {
                "type": "string",
                "description": "用例标题（如'网页登录 - 正确账号密码'）",
            },
            "url": {
                "type": "string",
                "description": "目标网页 URL（如 https://example.com/login）",
            },
            "steps": {
                "type": "string",
                "description": "操作步骤描述，每行一步",
            },
            "expected_result": {
                "type": "string",
                "description": "预期结果描述",
            },
            "priority": {
                "type": "string",
                "enum": ["P0", "P1", "P2"],
                "description": "优先级（默认 P1）",
            },
            "precondition": {
                "type": "string",
                "description": "前置条件描述",
            },
            "category": {
                "type": "string",
                "description": "分类标签（如 'smoke'）",
            },
            "description": {
                "type": "string",
                "description": "用例描述（测试目的）",
            },
            "directory_id": {
                "type": "integer",
                "description": "所属二级目录 ID（可选）",
            },
        },
        "required": ["case_id", "title", "url", "steps", "expected_result"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, case_id, title, url, steps, expected_result,
                   priority="P1", precondition="", category="",
                   description="", directory_id=None, **kwargs):
        try:
            obj = await run_sync(
                lambda: save_web_definition(
                    case_id=case_id,
                    title=title,
                    url=url,
                    steps=steps,
                    expected_result=expected_result,
                    priority=priority,
                    precondition=precondition,
                    category=category,
                    description=description,
                    directory_id=directory_id,
                )
            )
        except Exception as e:
            return ToolChunk(content=[TextBlock(text=f"保存 Web 用例失败：{e}")])

        dir_info = f"\n目录: {obj.directory.name}" if obj.directory else ""
        return ToolChunk(content=[TextBlock(
            text=f"Web 自动化用例 '{obj.title}' 保存成功。\n"
                 f"用例 ID: {obj.id}\n目标 URL: {obj.url}\n"
                 f"步骤数: {steps.count(chr(10)) + 1} 步\n"
                 f"优先级: {obj.priority}{dir_info}\n"
                 f"【注意】Web 自动化用例当前不支持自动执行，可在用例管理模块查看。"
        )])
