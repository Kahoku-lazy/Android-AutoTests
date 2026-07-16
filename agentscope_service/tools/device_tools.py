"""Device tools — manage the device pool for test execution."""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from ..adapters import DeviceAdapter
from .db_helper import run_sync


class GetOnlineDevicesTool(ToolBase):
    """List all online devices in the pool."""
    name = "get_online_devices"
    description = """查询平台当前在线的 Android 设备池。

【触发条件】当用户询问以下问题时，**必须**调用此工具（禁止凭记忆或猜测回答）：
  - "有几台设备连接？" / "多少台设备在线？"
  - "哪些设备在线？" / "设备状态是什么？"
  - "有空闲设备吗？" / "设备是否可用？"
  - 准备执行测试前（必须先确认有在线设备）

【返回数据】
  - serial: 设备序列号（用于 acquire_device）
  - model: 设备型号
  - status: ONLINE（空闲）/ BUSY（占用）/ OFFLINE（离线）
  - android_version: Android 版本
  - connection_type: USB / WIFI 连接方式

【使用示例】
  用户: "现在有哪几台设备可以用？"
  调用: get_online_devices()
  根据返回的 serial + status 回答用户

【约束】
  - 所有设备数据都来自平台数据库，禁止凭记忆回答
  - 如返回空列表，提示用户检查设备连接"""
    input_schema = {
        "type": "object",
        "properties": {},
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, **kwargs):
        try:
            devices = await run_sync(lambda: DeviceAdapter.get_online_devices())
        except Exception as e:
            return ToolChunk(content=[TextBlock(
                text=f"查询设备失败：{e}。请稍后重试。"
            )])
        if not devices:
            return ToolChunk(content=[TextBlock(
                text="当前没有在线设备。\n建议：1) 检查设备 USB 连接 2) 重启 ADB 服务 (adb kill-server && adb start-server)"
            )])
        lines = [
            f"- [{d.serial}] {d.model or '?'} | status={d.status} "
            f"| android={d.android_version or '?'} | 连接={d.connection_type or '?'}"
            for d in devices
        ]
        return ToolChunk(content=[TextBlock(
            text=f"在线设备 ({len(devices)}):\n" + "\n".join(lines)
        )])


class AcquireDeviceTool(ToolBase):
    """Lock a device for exclusive use during testing."""
    name = "acquire_device"
    description = """锁定一台在线设备用于独占测试执行。

【触发条件】
  - 执行 run_test 前**必须**先锁定设备
  - 设备状态为 ONLINE 时才能锁定，OFFLINE 或 BUSY 会失败
  - 建议先用 get_online_devices 确认设备在线再锁定

【参数说明】
  - serial: 设备序列号（从 get_online_devices 获取）
  - timeout: 锁定超时秒数，默认300秒（测试执行期间不会超时）

【返回值】
  - 成功 → 返回锁定的设备信息和剩余时间
  - 失败 → 返回具体原因（设备离线/已被占用/超时）

【重要约束】
  - 设备被锁定后会标记为 BUSY，其他测试无法使用
  - 测试执行完毕后，**必须**调用 release_device 释放锁
  - 不释放设备会导致设备资源泄漏，其他测试无法使用"""
    input_schema = {
        "type": "object",
        "properties": {
            "serial": {
                "type": "string",
                "description": "设备序列号（从 get_online_devices 获取，例如 'RF8N21MSW7A'）。"
            },
            "timeout": {
                "type": "integer",
                "description": "锁定超时秒数（默认300秒）。",
            },
        },
        "required": ["serial"],
    }
    is_concurrency_safe = False
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, serial, timeout=300, **kwargs):
        try:
            result = await run_sync(
                lambda: DeviceAdapter.acquire_device(
                    serial,
                    user_id=getattr(getattr(self, "_ctx", None), "user_id", None) or "ai_agent",
                    timeout=timeout,
                )
            )
            return ToolChunk(content=[TextBlock(
                text=f"设备 {serial} 已锁定。\n锁定时间: {result.get('locked_at')}\n超时时间: {result.get('timeout')}s\n\n【后续操作】请调用 run_test 执行测试，执行完毕后记得调用 release_device 释放设备。"
            )])
        except ValueError as e:
            return ToolChunk(content=[TextBlock(
                text=f"无法锁定设备 {serial}: {e}\n\n建议：1) 用 get_online_devices 确认设备在线 2) 等待设备空闲后重试"
            )])


class ReleaseDeviceTool(ToolBase):
    """Release a previously locked device."""
    name = "release_device"
    description = """将已锁定的设备释放回设备池，供其他测试使用。

【触发条件】
  - run_test 执行完毕后，**必须**调用此工具释放设备
  - 用户主动要求释放设备
  - 设备出现异常无法继续测试时

【参数说明】
  - serial: 要释放的设备序列号
  - reason: 释放原因（默认 'ai_release'），可选 'completed' / 'failed' / 'manual'

【返回值】
  - 成功 → 设备状态恢复为 ONLINE
  - 失败 → 设备未被锁定或已离线

【重要约束】
  - **不释放设备会导致资源泄漏**，其他测试无法使用该设备
  - 建议在 run_test 返回结果后，立即调用此工具"""
    input_schema = {
        "type": "object",
        "properties": {
            "serial": {
                "type": "string",
                "description": "要释放的设备序列号。",
            },
            "reason": {
                "type": "string",
                "description": "释放原因（默认 'ai_release'）。",
            },
        },
        "required": ["serial"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, serial, reason="ai_release", **kwargs):
        ok = await run_sync(lambda: DeviceAdapter.release_device(serial, reason=reason))
        return ToolChunk(content=[TextBlock(
            text=f"设备 {serial} {'已释放（状态恢复为 ONLINE）' if ok else '释放失败（可能未被锁定或已离线）'}。"
            + ("其他测试现在可以使用该设备。" if ok else "")
        )])
