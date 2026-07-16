"""Runner tools — execute and monitor test runs."""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from apps.test_runner.api import get_run_results, list_active_runs, stop_run
from apps.test_runner.runner import TestRunner
from apps.test_runner.callbacks import TestRunnerCallback
from models.test_models import TestCaseDef, TestRun
from .db_helper import run_sync


class RunTestTool(ToolBase):
    """Start a test run on a device with the specified test cases."""
    name = "run_test"
    description = """在指定设备上执行测试用例。

【触发条件】
  - 用户要求执行测试时
  - 用户说"跑一下这个用例" / "执行测试" / "开始测试"
  - debug_test_case 检查通过后建议执行

【完整执行流程】（必须按顺序执行）
  ① get_online_devices          → 确认有设备在线
  ② acquire_device(serial)      → 锁定设备（必须先锁定！）
  ③ run_test(...)               → 执行测试
  ④ release_device(serial)       → 释放设备（执行后必须释放！）

【参数说明】
  - run_id: 唯一运行标识（可使用 UUID）
  - serial: 设备序列号（从 get_online_devices 获取，**必须先 acquire_device**）
  - case_ids: 测试用例 ID 列表（从 list_test_cases 获取）
  - loop_count: 循环次数（默认1）
  - package_name: Android 包名（默认从第一个用例继承）

【返回值】
  - 执行状态：completed / failed
  - 通过/失败用例数量
  - 总执行时长

【重要约束】
  - **必须先调用 acquire_device 锁定设备**，否则执行会失败
  - **执行完毕后必须调用 release_device**，否则设备会被永久锁定！
  - 如果设备 BUSY 或离线，acquire_device 会报错"""
    input_schema = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "唯一运行标识（可使用 UUID，例如 'run-xxx-001'）。",
            },
            "serial": {
                "type": "string",
                "description": "设备序列号（必须先用 acquire_device 锁定）。",
            },
            "case_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要执行的测试用例 ID 列表（从 list_test_cases 获取）。",
            },
            "loop_count": {
                "type": "integer",
                "description": "循环执行次数（默认1）。",
            },
            "package_name": {
                "type": "string",
                "description": "目标 Android 包名（默认从第一个用例继承）。",
            },
        },
        "required": ["run_id", "serial", "case_ids"],
    }
    is_concurrency_safe = False
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, run_id, serial, case_ids, loop_count=1, package_name="", **kwargs):
        from apps.case_manager.api import get_definition
        from apps.device_pool.api import device as dpool

        # Build test case definitions
        test_cases = []
        for cid in case_ids:
            try:
                cdef = await run_sync(lambda c=cid: get_definition(c))
            except Exception as e:
                return ToolChunk(content=[TextBlock(
                    text=f"查询用例 '{cid}' 失败：{e}"
                )])
            if cdef is None:
                return ToolChunk(content=[TextBlock(
                    text=f"测试用例 '{cid}' 不存在。请先用 list_test_cases 确认用例 ID。"
                    + "\n\n【执行流程】get_online_devices → acquire_device → run_test → release_device"
                )])
            import json
            try:
                steps_data = json.loads(cdef.steps_json) if cdef.steps_json else []
            except Exception:
                steps_data = []
            from models.step_types import TestStep
            test_cases.append(TestCaseDef(
                id=cdef.id,
                title=cdef.title,
                category=cdef.category,
                description=cdef.description,
                steps=cdef.steps,
                steps_data=[TestStep.from_dict(s) for s in steps_data],
                enabled=True,
                is_json=True,
                package_name=cdef.package_name or package_name,
            ))

        if not package_name and test_cases:
            package_name = test_cases[0].package_name

        # Switch device
        await run_sync(lambda: dpool.switch_to(serial))
        runner = TestRunner(
            device=dpool,
            package_name=package_name,
            callback=TestRunnerCallback(),
        )

        success = await runner.run(run_id, test_cases, loop_count)
        status = "completed" if success else "failed"
        results = await run_sync(lambda: get_run_results(run_id))
        passed = sum(1 for r in results if r.result == 'pass')
        failed = sum(1 for r in results if r.result == 'fail')

        return ToolChunk(content=[TextBlock(
            text=f"测试执行 {status}。\n设备: {serial}\n用例数: {len(test_cases)}\n循环: {loop_count}\n"
            f"结果: 通过={passed} 失败={failed}\n\n"
            f"【后续】请调用 release_device(serial='{serial}') 释放设备！"
        )])


class GetRunResultsTool(ToolBase):
    """Fetch results of a completed or running test execution."""
    name = "get_run_results"
    description = """获取指定测试执行的结果详情。

【触发条件】
  - run_test 执行完毕后想查看详细结果
  - 用户询问"测试结果是什么？" / "跑了几个通过？"
  - 需要查看某个用例的耗时或失败原因

【参数说明】
  - run_id: 测试运行 ID（由 run_test 返回）

【返回数据】
  - 每个用例的执行结果：pass / fail
  - 迭代次数（loop_count > 1 时）
  - 每个用例的执行时长（毫秒）

【使用示例】
  调用: get_run_results(run_id="xxx")
  返回所有用例的通过/失败情况和耗时"""
    input_schema = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "测试运行 ID（由 run_test 返回）。",
            },
        },
        "required": ["run_id"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, run_id, **kwargs):
        results = await run_sync(lambda: get_run_results(run_id))
        if not results:
            return ToolChunk(content=[TextBlock(text=f"没有找到运行 ID '{run_id}' 的结果。可能测试尚未执行或 ID 不正确。")])
        lines = []
        for r in results:
            lines.append(f"- [{r.result}] {r.case_title} | 迭代={r.iteration} | 耗时={r.duration_ms}ms")
        passed = sum(1 for r in results if r.result == 'pass')
        failed = sum(1 for r in results if r.result == 'fail')
        summary = f"运行: {run_id} | 总计: {len(results)} | 通过={passed} 失败={failed}"
        return ToolChunk(content=[TextBlock(text=summary + "\n" + "\n".join(lines))])


class StopRunTool(ToolBase):
    """Stop an active test run."""
    name = "stop_run"
    description = """停止正在执行的测试运行。

【触发条件】
  - 测试执行时间过长需要中止
  - 用户说"停止测试" / "中止执行"
  - 设备出现异常需要终止测试"""
    input_schema = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "要停止的测试运行 ID。",
            },
        },
        "required": ["run_id"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, run_id, **kwargs):
        ok = await run_sync(lambda: stop_run(run_id))
        return ToolChunk(content=[TextBlock(
            text=f"测试 '{run_id}' {'已停止' if ok else '未找到或已结束'}。"
            + ("设备已被自动释放，可用于其他测试。" if ok else "")
        )])
