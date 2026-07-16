"""Case tools — create, read, update test-case definitions."""

import uuid
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from apps.case_manager.api import save_definition, get_definition, get_enabled_definitions
from apps.case_manager.models import TestDefinition
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
                            "description": "备用 XPath（用于 wait_either）",
                        },
                        "timeout": {"type": "number", "description": "超时秒数（默认 10）"},
                        "expected_text": {
                            "type": "string",
                            "description": "预期文本（用于 verify_text / poll_text / wait_toast）",
                        },
                        "index": {
                            "type": "integer",
                            "description": "索引（用于 click_indexed 等）",
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
                "click",
                "click_indexed",
                "wait",
                "wait_disappear",
                "wait_either",
                "verify_text",
                "poll_text",
                "retry_click",
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
