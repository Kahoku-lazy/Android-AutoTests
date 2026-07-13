"""Task tools — create runner task cards from AI conversations."""
import json
import uuid
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock, HintBlock
from .db_helper import run_sync


class FetchPageElementsTool(ToolBase):
    """Fetch all elements belonging to a page, with their XPath candidates."""
    name = "fetch_page_elements"
    description = "Get all UI elements on a specific page, with their XPath locators. Use this to find elements for test case steps. Pass a page_id or search by page label."
    input_schema = {
        "type": "object",
        "properties": {
            "page_id": {
                "type": "integer",
                "description": "Page ID to fetch elements from (optional if page_label is given)."
            },
            "page_label": {
                "type": "string",
                "description": "Search by page label/name instead of ID."
            },
            "limit": {
                "type": "integer",
                "description": "Max elements to return (default 30)."
            },
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, page_id=None, page_label=None, limit=30, **kwargs):
        from apps.element_locator.models import Element, Page

        def _fetch_elements():
            qs = Element.objects.select_related('page')
            if page_id:
                qs = qs.filter(page_id=page_id)
            elif page_label:
                qs = qs.filter(page__label__icontains=page_label)
            return list(qs[:limit])

        qs = await run_sync(_fetch_elements)
        if not qs:
            hint = f"page_id={page_id}" if page_id else f"page_label='{page_label}'"
            return ToolChunk(content=[TextBlock(
                text=f"No elements found for {hint}. "
                     + "Tip: use the element locator module to dump UI and capture elements for this page first."
            )])

        lines = []
        for el in qs:
            try:
                xpath_cands = json.loads(el.xpath_candidates) if el.xpath_candidates else []
                best_xpath = xpath_cands[0]['xpath'] if xpath_cands else '?'
                count = xpath_cands[0]['count'] if xpath_cands else 0
            except Exception:
                best_xpath = '?'
                count = 0
            lines.append(
                f"- [{el.id}] text='{el.text_val or ''}' class={el.class_name} "
                f"res_id={el.resource_id} xpath={best_xpath} (matches:{count}) "
                f"page={el.page.label if el.page else '?'}"
            )

        page_name = qs[0].page.label if qs[0].page else "?"
        return ToolChunk(content=[TextBlock(
            text=f"Elements on page '{page_name}' ({len(qs)}):\n"
                 + "\n".join(lines)
                 + "\n\nUse the xpath values as locators in save_test_case steps."
        )])


class CreateTestSOPTool(ToolBase):
    """Create a Test SOP context — initiates the 4-phase workflow.

    Call this when user confirms the case design and you're ready to start Phase 2.
    The SOP context persists across all 4 phases and links to the final task card.
    """
    name = "create_test_sop"
    description = """创建测试 SOP 上下文记录，标记需求确认完毕，进入元素准备阶段。

【何时调用】
- 第一阶段（需求分析）完成，用户确认用例设计方案后
- 告诉 AI："需求已确认，开始准备元素"

【参数说明】
- requirement: 用户测试需求摘要（字符串）
- case_design: 用例设计方案（JSON 数组，每个元素含 name/description/steps）

【返回】
- sop_id：SOP 上下文唯一标识（格式 sop-xxxxxxxx）
- 一个 HintBlock 会被前端渲染成 SOP 状态卡片

【后续阶段】
- 第二阶段：AI 调用 fetch_page_elements 检查元素，缺失时告知用户
- 第三阶段：AI 调用 save_test_case 创建用例 + debug_test_case 调试
- 第四阶段：AI 调用 create_runner_task（传入 sop_id）创建任务并执行
"""
    input_schema = {
        "type": "object",
        "properties": {
            "requirement": {
                "type": "string",
                "description": "用户测试需求摘要（简洁描述要测什么）",
            },
            "case_design": {
                "type": "string",
                "description": "用例设计方案，JSON 数组字符串。字段：name(用例名)/description(描述)/steps(操作步骤数组)",
            },
        },
        "required": ["requirement", "case_design"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, requirement, case_design, **kwargs):
        from apps.test_runner.models import TestSOP

        sop_id = f"sop-{uuid.uuid4().hex[:8]}"

        # Parse case_design JSON
        try:
            case_list = json.loads(case_design) if isinstance(case_design, str) else case_design
        except json.JSONDecodeError:
            return ToolChunk(content=[TextBlock(
                text="case_design 格式错误，请提供有效的 JSON 数组。"
                     + '示例：[{"name":"用例1","description":"描述","steps":["步骤1","步骤2"]}]'
            )])

        sop = await run_sync(lambda: TestSOP.objects.create(
            sop_id=sop_id,
            phase=1,
            status='active',
            requirement=requirement,
            case_design=case_list,
        ))

        case_names = [c.get("name", "?") for c in case_list]

        hint_data = {
            "type": "sop_card",
            "sop_id": sop_id,
            "phase": 1,
            "phase_label": "需求已确认",
            "requirement": requirement,
            "case_design": case_list,
            "case_count": len(case_list),
            "case_names": case_names,
            "element_mapping": [],
            "element_gaps": [],
            "case_ids": [],
            "run_id": "",
            "status": "active",
            "next_hint": "进入第二阶段：元素准备 → 检查用例所需的页面元素是否存在",
        }
        return ToolChunk(content=[
            TextBlock(text=(
                f"✅ SOP 上下文已创建 (ID: {sop_id})\n"
                f"需求：{requirement}\n"
                f"用例设计：{len(case_list)} 个\n"
                + "  " + "\n  ".join(f"{i+1}. {n}" for i, n in enumerate(case_names))
                + "\n\n"
                f"【第二阶段】请调用 fetch_page_elements 检查每个用例所需的页面元素是否存在。\n"
                f"若元素缺失，请告知用户并记录到 element_gaps。\n\n"
                f"建议：先用 TaskCreate 为第二阶段创建子任务（每个用例一个检查任务），"
                f"逐步完成后用 TaskUpdate 标记，全部完成后再调用 update_test_sop 推进。"
            )),
            HintBlock(id=f"sop-card-{sop_id}", hint=json.dumps(hint_data, ensure_ascii=False)),
        ])


class UpdateTestSOPTool(ToolBase):
    """Update Test SOP context — advance phase or record phase outputs."""
    name = "update_test_sop"
    description = """更新测试 SOP 上下文状态，记录当前阶段产出，推进到下一阶段。

【何时调用】
- 第二阶段完成（元素检查完毕）→ 传入 element_mapping / element_gaps
- 第三阶段完成（用例调试通过）→ 传入 case_ids
- 第四阶段完成（执行完毕）→ 传入 run_results 并标记 status='completed'
- 用户取消 → 传入 status='cancelled'

【参数说明】
- sop_id: 要更新的 SOP ID
- phase: 当前阶段（2/3/4）
- element_mapping: 元素映射表（JSON 数组，phase=2 时填写）
- element_gaps: 缺失元素列表（JSON 数组，phase=2 时填写）
- case_ids: 调试通过的用例 ID 列表（phase=3 时填写）
- run_id: 关联的任务执行 ID（phase=4 时填写）
- run_results: 执行结果摘要（phase=4 时填写）
- status: 'active' | 'completed' | 'cancelled'
"""
    input_schema = {
        "type": "object",
        "properties": {
            "sop_id": {
                "type": "string",
                "description": "SOP 上下文 ID（格式 sop-xxxxxxxx）",
            },
            "phase": {
                "type": "integer",
                "description": "当前阶段：2（元素准备）/ 3（用例创建）/ 4（任务执行）",
            },
            "element_mapping": {
                "type": "string",
                "description": "元素映射表，JSON 数组字符串（phase=2 时填写）",
            },
            "element_gaps": {
                "type": "string",
                "description": "缺失元素列表，JSON 数组字符串（phase=2 时填写）",
            },
            "case_ids": {
                "type": "string",
                "description": "调试通过的用例 ID 列表，JSON 数组字符串（phase=3 时填写）",
            },
            "run_id": {
                "type": "string",
                "description": "关联的任务执行 ID（phase=4 时填写）",
            },
            "run_results": {
                "type": "string",
                "description": "执行结果摘要，JSON 对象字符串（phase=4 时填写）",
            },
            "status": {
                "type": "string",
                "enum": ["active", "completed", "cancelled"],
                "description": "SOP 状态",
            },
        },
        "required": ["sop_id", "phase"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, sop_id, phase, element_mapping=None, element_gaps=None,
                   case_ids=None, run_id=None, run_results=None, status=None, **kwargs):
        from apps.test_runner.models import TestSOP

        sop = await run_sync(lambda: TestSOP.objects.filter(sop_id=sop_id).first())
        if not sop:
            return ToolChunk(content=[TextBlock(text=f"SOP '{sop_id}' 不存在。")])

        sop.phase = phase
        if status:
            sop.status = status
        if element_mapping is not None:
            sop.element_mapping = json.loads(element_mapping) if isinstance(element_mapping, str) else element_mapping
        if element_gaps is not None:
            sop.element_gaps = json.loads(element_gaps) if isinstance(element_gaps, str) else element_gaps
        if case_ids is not None:
            sop.case_ids = json.loads(case_ids) if isinstance(case_ids, str) else case_ids
        if run_id:
            sop.run_id = run_id
        if run_results is not None:
            sop.run_results = json.loads(run_results) if isinstance(run_results, str) else run_results

        await run_sync(lambda: sop.save())

        phase_labels = {2: "元素准备", 3: "用例创建", 4: "任务执行"}
        phase_hint = {
            2: "请逐一检查用例所需页面元素是否存在，缺失时告知用户。",
            3: "请调用 save_test_case 创建用例，然后 debug_test_case 调试。",
            4: "请锁定设备、执行测试、释放设备。",
        }

        if status == 'completed':
            result_text = (
                f"✅ SOP {sop_id} 测试完成！\n\n"
                f"建议：调用 TaskList 查看本阶段子任务清单，确认所有子任务已完成。"
            )
        elif status == 'cancelled':
            result_text = f"❌ SOP {sop_id} 已取消。"
        else:
            result_text = (
                f"✅ SOP {sop_id} 已更新 → 阶段 {phase}（{phase_labels.get(phase, '?')}）\n\n"
                f"{phase_hint.get(phase, '')}\n\n"
                f"建议：调用 TaskList 查看当前子任务状态，"
                f"用 TaskCreate 为本阶段创建新的子任务，逐步完成后用 TaskUpdate 标记。"
            )

        return ToolChunk(content=[TextBlock(text=result_text)])


class CreateRunnerTaskTool(ToolBase):
    """Create a test-runner task card linked to a Test SOP workflow.

    loop_count defaults to 3 for AI-created tasks (AI assistant rule).
    If sop_id is provided, links this task to the SOP context.
    """
    name = "create_runner_task"
    description = """创建可执行的任务卡片（核心！）。

【功能说明】
- 创建可见的任务卡片，用户可在执行引擎中查看和执行
- 若传入 sop_id，自动关联到对应的 Test SOP 工作流
- loop_count 默认 3 次（AI 助手规则），用户未指定时保持此值

【参数说明】
- task_name: 任务名称
- device_serial: 设备序列号（必须先用 get_online_devices + acquire_device 锁定）
- case_ids: 用例 ID 列表（必须是已调试通过的用例！）
- loop_count: 循环次数（**默认 3**，AI 助手规则）
- sop_id: 可选，关联的 SOP 上下文 ID（格式 sop-xxxxxxxx）
- start_immediately: 是否立即开始执行（默认 false）
"""
    input_schema = {
        "type": "object",
        "properties": {
            "task_name": {
                "type": "string",
                "description": "任务名称（建议与 SOP 需求相关）",
            },
            "device_serial": {
                "type": "string",
                "description": "设备序列号（必须先用 acquire_device 锁定）",
            },
            "case_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "调试通过的用例 ID 列表",
            },
            "loop_count": {
                "type": "integer",
                "description": "循环执行次数（默认 3 次，AI 助手规则）",
            },
            "sop_id": {
                "type": "string",
                "description": "关联的 SOP 上下文 ID（可选，格式 sop-xxxxxxxx）",
            },
            "start_immediately": {
                "type": "boolean",
                "description": "是否立即执行（默认 false，用户手动开始）",
            },
        },
        "required": ["task_name", "device_serial", "case_ids"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, task_name, device_serial, case_ids, loop_count=3,
                   sop_id=None, start_immediately=False, **kwargs):
        from apps.test_runner.models import TestRunRecord, TestSOP

        # Validate cases exist
        from apps.case_manager.api import get_definition
        missing = []
        for cid in case_ids:
            try:
                if await run_sync(lambda c=cid: get_definition(c) is None):
                    missing.append(c)
            except Exception:
                missing.append(cid)
        if missing:
            return ToolChunk(content=[TextBlock(
                text=f"Cannot create task: cases not found: {missing}. "
                     + "Use list_test_cases to see available cases."
            )])

        # Validate device
        from apps.device_pool.models import Device
        device = await run_sync(lambda: Device.objects.filter(serial=device_serial).first())
        if not device:
            return ToolChunk(content=[TextBlock(
                text=f"Device '{device_serial}' not found. Use get_online_devices to see available devices."
            )])

        run_id = f"ai-task-{uuid.uuid4().hex[:8]}"
        record = await run_sync(lambda: TestRunRecord.objects.create(
            run_id=run_id,
            status="PENDING",
            device_serial=device_serial,
            selected_cases=case_ids,
            loop_count=loop_count,
        ))

        # Link to SOP context if provided
        if sop_id:
            sop = await run_sync(lambda: TestSOP.objects.filter(sop_id=sop_id).first())
            if sop:
                sop.run_id = run_id
                sop.phase = 4
                await run_sync(lambda: sop.save())

        # Build case summaries
        case_summaries = []
        case_titles = []
        for cid in case_ids:
            cdef = await run_sync(lambda c=cid: get_definition(c))
            steps_count = 0
            try:
                steps_data = json.loads(cdef.steps_json) if cdef.steps_json else []
                steps_count = len(steps_data)
            except Exception:
                pass
            case_summaries.append(f"  - {cdef.title} ({steps_count} steps)")
            case_titles.append(cdef.title)

        result = (
            f"Task card created!\n"
            f"Task: {task_name}\n"
            f"Run ID: {run_id}\n"
            f"Device: {device_serial} ({device.model or device.name})\n"
            f"Cases: {len(case_ids)}\n"
            f"Loops: {loop_count} (AI assistant default)\n\n"
            f"Cases:\n" + "\n".join(case_summaries) + "\n\n"
            f"The task is now visible in the execution engine. "
            f"You can call run_test with run_id='{run_id}' to start it now."
        )

        hint_data = {
            "type": "task_card",
            "task_id": run_id,
            "title": task_name,
            "status": "PENDING",
            "device": device_serial,
            "device_model": device.model or device.name or "",
            "cases": case_ids,
            "case_titles": case_titles,
            "loop_count": loop_count,
            "run_id": run_id,
            "sop_id": sop_id or "",
            "progress": {"current": 0, "total": len(case_ids) * loop_count},
            "actions": ["view_detail", "start", "rerun"],
        }
        return ToolChunk(content=[
            TextBlock(text=result),
            HintBlock(id=f"task-card-{run_id}", hint=json.dumps(hint_data, ensure_ascii=False)),
        ])


class ListAITasksTool(ToolBase):
    """List AI-created task cards with their status and results."""
    name = "list_ai_tasks"
    description = """列出 AI 创建的测试任务卡片历史。

何时使用：
- 用户问"我创建了哪些任务"、"查看历史任务"
- 用户问"上次测试结果是什么"
- 用户想继续之前未完成的任务
- 用户问"有哪些测试在跑"

返回：任务名称、状态(PENDING/RUNNING/COMPLETED/FAILED)、设备、用例数量、开始时间、结果摘要。
每个任务都有唯一的 run_id（格式：ai-task-xxxxxxxx）。"""
    input_schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "running", "completed", "failed", "all"],
                "description": "按状态过滤（默认 all）",
            },
            "limit": {
                "type": "integer",
                "description": "最多返回数量（默认 20）",
            },
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, status="all", limit=20, **kwargs):
        from apps.test_runner.models import TestRunRecord

        def _fetch_tasks():
            qs = TestRunRecord.objects.filter(run_id__startswith="ai-task-").order_by("-started_at")
            if status != "all" and status:
                qs = qs.filter(status__iexact=status)
            return list(qs[:limit])

        qs = await run_sync(_fetch_tasks)

        if not qs:
            return ToolChunk(content=[TextBlock(
                text="暂无历史任务。告诉用户可以通过 AI 助手创建新的测试任务。"
            )])

        lines = []
        for r in qs:
            cases_count = len(r.selected_cases) if r.selected_cases else 0
            started = r.started_at.strftime('%Y-%m-%d %H:%M') if r.started_at else '?'
            lines.append(
                f"- [{r.status}] {r.run_id}\n"
                f"  设备: {r.device_serial} | 用例: {cases_count} | 循环: {r.loop_count} | "
                f"开始: {started}"
            )

        summary = f"共 {len(qs)} 个任务"
        return ToolChunk(content=[TextBlock(text=summary + "\n" + "\n".join(lines))])


class UpdateAITaskTool(ToolBase):
    """Update the status of an AI-created task (used by the execution pipeline)."""
    name = "update_ai_task"
    description = """更新 AI 任务的状态（通常由执行管道自动调用，普通对话不需要）。

何时使用：
- 当 run_test 执行完毕后，需要更新任务状态为 COMPLETED/FAILED
- 当用户手动停止任务时，更新状态为 STOPPED
- 普通 AI 对话**不需要**调用此工具。"""
    input_schema = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "任务 run_id（如 ai-task-7f3a2c1d）",
            },
            "status": {
                "type": "string",
                "enum": ["PENDING", "RUNNING", "COMPLETED", "FAILED", "STOPPED"],
                "description": "任务新状态",
            },
            "progress_current": {
                "type": "integer",
                "description": "当前完成数（可选）",
            },
            "progress_total": {
                "type": "integer",
                "description": "总数量（可选）",
            },
        },
        "required": ["run_id", "status"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, run_id, status, progress_current=None, progress_total=None, **kwargs):
        from apps.test_runner.models import TestRunRecord

        record = await run_sync(lambda: TestRunRecord.objects.filter(run_id=run_id).first())
        if not record:
            return ToolChunk(content=[TextBlock(text=f"任务 '{run_id}' 不存在。")])

        record.status = status
        await run_sync(lambda: record.save())

        return ToolChunk(content=[TextBlock(text=f"任务 {run_id} 已更新为状态：{status}")])
