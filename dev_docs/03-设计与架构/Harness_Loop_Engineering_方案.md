# Harness Engineering + Loop Engineering 实施方案

> 基于 AgentScope 2.0，为 Android-AutoTests 平台设计的智能体工程化方案

---

## 一、现状分析

### 1.1 已有能力

| 组件 | 状态 | 说明 |
|------|------|------|
| 17 个业务工具 | ✅ 已实现 | device / case / runner / report / RAG / task |
| `build_business_tools()` | ✅ 正常 | 工具注册链路通 |
| AgentScope Toolkit | ✅ 正常 | `get_toolkit(extra_factory=...)` 正确传入 |
| `AIAgent.system_prompt` | ⚠️ 太通用 | 默认值："你是一个有用的AI测试助手。" |
| 工具 description | ⚠️ 缺乏触发条件 | LLM 不知道何时该调用 |
| 会话历史持久化 | ❌ 未实现 | AIAgent.memory_mode='inmemory'，每次重建 Agent 历史丢失 |
| 定时自动化 | ❌ 未实现 | 没有 Loop 触发机制 |
| 工具调用日志 | ⚠️ 半成品 | `AIExecutionLog` 模型存在但未写入 |

### 1.2 根本问题

**Harness 不完善 → LLM 不选工具 → 凭记忆回答 → 答案不可信**

```
用户: "当前有几台设备连接？"
  ↓
LLM 推理:  → "根据我的知识...大约3-5台设备..."
  ↓
未调用 get_online_devices → 返回过时/错误数据
```

---

## 二、Harness Engineering — 智能体工程层

> 目标：让 LLM **精准选择工具**，获取**实时平台数据**

### 2.1 增强系统提示词（平台上下文）

**文件**: `apps/ai_assistant/models.py` — 修改 `system_prompt` 默认值

**修改方式**: 在 Django Admin 中修改 AIAgent 记录，或修改 `agent_factory.py` 动态拼接

```python
# apps/ai_assistant/models.py — 修改 system_prompt 默认值
system_prompt = models.TextField(
    default='',
    # ← 删除这行旧默认值，在 agent_factory.py 中动态注入
)
```

```python
# agentscope_service/agent_factory.py — 动态拼接增强提示词
def build_agent_from_db(agent_id: int, user_id: str) -> Agent:
    # ... 现有代码 ...

    # 平台上下文基座提示词（固定前缀，所有 Agent 共享）
    PLATFORM_CONTEXT = """你运行在一个 Android 自动化测试平台上。

【平台能力约束】（以下规则必须遵守）
1. 平台数据只能通过工具获取：设备池状态、测试用例、运行结果、报告等
   所有数据都存储在平台数据库中，**禁止凭记忆或猜测回答**
2. 工具是唯一真实数据源：调用 get_online_devices 才能知道设备状态
3. 当用户询问任何平台相关数据时，必须先调用对应工具获取实时数据
4. 当工具返回空结果时，如实告知用户并给出建议

【工具选择策略】
- 问"有几台/哪些/什么设备" → get_online_devices
- 问测试用例数量/列表 → list_test_cases
- 问测试结果/报告 → get_run_results / list_reports
- 问某用例详情 → get_test_case
- 需要执行测试 → run_test
- 需要先查设备再执行 → get_online_devices → acquire_device → run_test
- 设备忙/离线 → release_device 释放锁
"""

    db_system = db_agent.system_prompt or ''
    # 如果用户在 Admin 中设置了自定义提示词，追加平台约束
    if db_system:
        system_prompt = db_system + "\n\n" + PLATFORM_CONTEXT
    else:
        system_prompt = PLATFORM_CONTEXT
```

### 2.2 触发式工具描述（核心改动）

**文件**: `agentscope_service/tools/device_tools.py`

每个工具的 description 字段改为结构化格式，包含：
- **触发条件**: 何时必须调用
- **数据约束**: 返回什么、禁止什么
- **调用前置**: 调用前需要什么

```python
# agentscope_service/tools/device_tools.py

class GetOnlineDevicesTool(ToolBase):
    name = "get_online_devices"
    description = """查询平台当前在线的 Android 设备池。

【触发条件】当用户询问以下问题时，必须调用此工具（禁止凭记忆回答）：
  - "有几台设备连接？" / "多少台设备在线？"
  - "哪些设备在线？" / "设备状态是什么？"
  - "设备是否可用？" / "有空闲设备吗？"
  - 准备执行测试前（必须先确认有在线设备）

【返回数据】
  - serial: 设备序列号（用于 acquire_device）
  - model: 设备型号
  - status: ONLINE（空闲）/ BUSY（占用）/ OFFLINE（离线）
  - android_version: Android 版本

【使用示例】
  问: "现在有哪几台设备可以用？"
  调用: get_online_devices()
  根据返回的 serial + status 回答用户
"""
    input_schema = {
        "type": "object",
        "properties": {},
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Read-only device listing.")

    async def call(self, **kwargs):
        devices = get_online_devices()
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
    name = "acquire_device"
    description = """锁定一台在线设备用于独占测试执行。

【触发条件】
  - 执行 run_test 前必须先锁定设备
  - 设备状态为 ONLINE 时才能锁定，OFFLINE 或 BUSY 会失败

【参数说明】
  - serial: 设备序列号（从 get_online_devices 获取）
  - timeout: 锁定超时秒数，默认300秒

【返回值】
  成功 → 返回锁定的设备信息和剩余时间
  失败 → 返回具体原因（设备离线/已被占用/超时）
"""
    # ... 其余代码不变 ...
```

**文件**: `agentscope_service/tools/case_tools.py` — 同理增强 description

```python
class ListTestCasesTool(ToolBase):
    name = "list_test_cases"
    description = """列出平台中已启用的测试用例。

【触发条件】当用户询问以下问题时，必须调用此工具：
  - "有哪些测试用例？"
  - "测试用例总数？"
  - "我创建了哪些用例？"
  - 准备执行测试前（先确认用例存在）

【返回数据】
  - case_id: 用例唯一标识（用于 run_test）
  - title: 用例名称
  - category: 分类标签（smoke/regression 等）
  - package_name: 目标 Android 包名

【使用示例】
  问: "平台上有哪些测试用例？"
  调用: list_test_cases()
  调用: get_test_case(case_id="xxx")  # 如需查看某用例详情
"""
    # ... 其余代码不变 ...
```

### 2.3 工具工厂增强（可选 — 添加元工具描述）

**文件**: `agentscope_service/tools/factory.py`

在 `build_business_tools()` 返回的工具列表上方添加一个**平台元描述工具**，
当 LLM 需要了解"我有哪些能力"时，可以调用此工具获取完整能力清单：

```python
# agentscope_service/tools/factory.py

class PlatformCapabilitiesTool(ToolBase):
    """List all available platform capabilities and their trigger conditions."""
    name = "list_platform_capabilities"
    description = """列出平台所有可用能力。

【何时使用】当用户询问"你能做什么？"、"你会什么？"、
或你不确定该用哪个工具时，调用此工具获取完整能力清单。

【平台能力分类】
1. 设备管理：查询设备、锁定设备、释放设备
2. 测试用例：创建用例、查看用例列表、查看用例详情、调试用例
3. 测试执行：执行测试、查询结果、停止执行
4. 报告管理：生成报告、查看报告列表
5. 知识库：搜索技术文档、常见问题解答
6. 页面探索：获取页面元素、搜索元素

返回每个能力的触发条件、输入参数、返回数据说明。
"""
    input_schema = {"type": "object", "properties": {}}
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Read-only capabilities listing.")

    async def call(self, **kwargs):
        return ToolChunk(content=[TextBlock(text="Platform capabilities listed above.")])


async def build_business_tools(user_id: str, agent_id: str, session_id: str) -> list:
    """Factory: returns all business tools including the platform capabilities meta-tool."""
    return [
        # 元工具：帮助 LLM 了解自己有哪些能力
        PlatformCapabilitiesTool(),
        # 现有 17 个工具...
        GetOnlineDevicesTool(),
        AcquireDeviceTool(),
        ReleaseDeviceTool(),
        ListTestCasesTool(),
        GetTestCaseTool(),
        SaveTestCaseTool(),
        DebugTestCaseTool(),
        RunTestTool(),
        GetRunResultsTool(),
        StopRunTool(),
        SaveReportTool(),
        ListReportsTool(),
        KnowledgeBaseSearchTool(),
        GetTestPointsTool(),
        SearchElementsTool(),
        FetchPageElementsTool(),
        CreateRunnerTaskTool(),
    ]
```

---

## 三、Loop Engineering — 自主循环层

> 目标：让 Agent 具备**记忆**、**自触发**、**自我观察**能力

### 3.1 持久化记忆（会话历史 → 数据库）

**问题**: 当前 `memory_mode='inmemory'`，每次创建 Agent 实例历史全丢失

**解决**: 将 AIAgent.memory_mode 改为 `'longterm'`，并配置 Django ORM 作为记忆存储

**文件**: `agentscope_service/agent_factory.py`

```python
from agentscope.memory import MemoryWithRDBMS

def build_agent_from_db(agent_id: int, user_id: str) -> Agent:
    db_agent = AIAgent.objects.prefetch_related('tools').get(id=agent_id)

    # ... model 构建代码不变 ...

    # 记忆配置
    if db_agent.memory_mode == 'longterm':
        # 使用 Django DB 作为持久化记忆
        from agentscope.memory import MemoryWithRDBMS
        memory = MemoryWithRDBMS(
            db_path=str(settings.DATABASES['default']['NAME']),
            table_name='ai_messages',
            session_key=session_id,  # 每个会话独立的记忆
        )
    else:
        memory = None  # inmemory 模式

    agent = Agent(
        name=db_agent.name or "TestAssistant",
        system_prompt=system_prompt,
        model=model,
        toolkit=None,
        memory=memory,  # ← 传入持久化记忆
        # AgentScope 2.0 其他配置
        max_iters=db_agent.max_iters,
        parallel_tool_calls=db_agent.parallel_tool_calls,
    )
    return agent
```

**数据库表已存在**: `ai_messages` (role, content, tool_calls, tokens)

### 3.2 工具调用日志（自我观察）

**文件**: `agentscope_service/tools/base.py` — 新建基础工具类，注入日志写入

```python
"""agentscope_service/tools/base.py
基础工具类：为所有工具自动注入日志记录能力
"""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior


class LoggedToolBase(ToolBase):
    """所有业务工具的基类，自动将调用记录写入 AIExecutionLog"""

    async def call(self, **kwargs):
        # 记录调用开始
        from apps.ai_assistant.models import AIExecutionLog, AIAgent
        tool_name = self.name
        input_summary = str(kwargs)[:500]  # 截断避免过大

        log = AIExecutionLog.objects.create(
            agent_id=1,  # 动态获取当前 agent_id
            level='info',
            message=f"[TOOL CALL] {tool_name}",
            metadata=json.dumps({
                'input': input_summary,
                'timestamp': datetime.now().isoformat(),
            }),
        )

        try:
            result = await self._call_impl(**kwargs)
            # 记录成功
            AIExecutionLog.objects.filter(id=log.id).update(
                level='info',
                metadata=json.dumps({
                    **json.loads(log.metadata),
                    'status': 'success',
                    'output_length': len(str(result)),
                }),
            )
            return result
        except Exception as e:
            # 记录失败 + 触发重试
            AIExecutionLog.objects.filter(id=log.id).update(
                level='error',
                message=f"[TOOL ERROR] {tool_name}: {str(e)}",
                metadata=json.dumps({
                    **json.loads(log.metadata),
                    'status': 'error',
                    'error': str(e),
                }),
            )
            raise
```

**修改所有工具继承**: `from .base import LoggedToolBase` 替换 `from agentscope.tool import ToolBase`

### 3.3 自动化触发（Loop Triggers）

**场景驱动触发器**:

| 触发事件 | 自动执行动作 | 实现方式 |
|----------|------------|---------|
| 定时 (cron) | 生成设备状态报告推送给用户 | Django management command + WorkBuddy 自动化 |
| 设备 OFFLINE | 自动重连 + 通知用户 | Device 模型 signal + 消息推送 |
| 测试失败 (fail) | 自动重跑一次 + 告警 | TestRunnerCallback 扩展 |
| 用例 XPath 失效 | AI 自动尝试修复 XPath | `debug_test_case` 触发 |
| 长时间无会话 | 发送使用提示 | WorkBuddy 自动化 |

**文件**: `agentscope_service/loops/device_monitor.py` — 新建

```python
"""agentscope_service/loops/device_monitor.py
设备监控循环：当设备断连时自动触发重连流程
"""
from apps.device_pool.models import Device
from apps.ai_assistant.models import AIExecutionLog
import logging

logger = logging.getLogger(__name__)


def monitor_devices():
    """定时任务：检查设备状态，断连时记录日志并尝试重连"""
    devices = Device.objects.all()
    offline_alerts = []

    for device in devices:
        if device.status == 'OFFLINE':
            # 记录 OFFLINE 事件
            AIExecutionLog.objects.create(
                agent_id=1,
                level='warning',
                message=f"[DEVICE OFFLINE] {device.serial} - {device.model}",
                metadata='{"event": "device_offline", "serial": "%s"}' % device.serial,
            )
            offline_alerts.append(device)

            # 自动尝试重连（通过 ADB）
            _attempt_adb_reconnect(device.serial)

    if offline_alerts:
        logger.warning(f"{len(offline_alerts)} device(s) offline: {[d.serial for d in offline_alerts]}")
        # 可以触发 AI 通知用户

    return offline_alerts


def _attempt_adb_reconnect(serial: str):
    """通过 ADB 尝试重连指定设备"""
    import subprocess
    try:
        result = subprocess.run(
            ['adb', '-s', serial, 'get-state'],
            capture_output=True, text=True, timeout=5
        )
        # 如果设备状态改变，更新数据库
        if 'device' in result.stdout:
            Device.objects.filter(serial=serial).update(status='ONLINE')
            logger.info(f"Device {serial} reconnected automatically")
    except Exception as e:
        logger.error(f"ADB reconnect failed for {serial}: {e}")
```

### 3.4 自我修正 Loop（高阶）

当工具调用返回错误时，LLM 自动重试或换策略：

```python
# agentscope_service/agent_factory.py — 添加错误重试包装

def build_agent_from_db(agent_id: int, user_id: str) -> Agent:
    # ... 现有代码 ...

    # 包装工具的 call 方法，添加自动重试
    def wrap_tool_with_retry(tool):
        original_call = tool.call

        async def retried_call(**kwargs):
            last_error = None
            for attempt in range(2):  # 最多重试 1 次
                try:
                    return await original_call(**kwargs)
                except Exception as e:
                    last_error = e
                    if attempt == 0:
                        # 第一次失败，尝试恢复（如设备断连后重连）
                        logger.warning(f"Tool {tool.name} failed: {e}, retrying...")
                        await _recover_from_error(tool.name, kwargs)
                    else:
                        AIExecutionLog.objects.create(
                            agent_id=db_agent.id,
                            level='error',
                            message=f"[TOOL RETRY FAILED] {tool.name}: {e}",
                        )
            raise last_error

        tool.call = retried_call
        return tool

    # 应用重试包装到所有工具
    from agentscope_service.tools.factory import build_business_tools
    tools = await build_business_tools(user_id, str(agent_id), session_id)
    wrapped_tools = [wrap_tool_with_retry(t) for t in tools]

    # ... 构建 toolkit ...
```

---

## 四、完整文件变更清单

| 优先级 | 文件 | 改动类型 | 改动内容 |
|--------|------|----------|---------|
| **P0** | `agentscope_service/tools/device_tools.py` | 修改 | 增强 `get_online_devices` description 为触发式 |
| **P0** | `agentscope_service/tools/case_tools.py` | 修改 | 增强 `list_test_cases` 等工具 description |
| **P0** | `agentscope_service/tools/runner_tools.py` | 修改 | 增强 `run_test` / `get_run_results` description |
| **P1** | `agentscope_service/agent_factory.py` | 修改 | 动态注入平台上下文 + 记忆配置 |
| **P1** | `agentscope_service/tools/factory.py` | 修改 | 添加 `PlatformCapabilitiesTool` |
| **P2** | `agentscope_service/loops/device_monitor.py` | 新建 | 设备监控循环 |
| **P2** | `agentscope_service/tools/base.py` | 新建 | 工具日志基类 |
| **P2** | `apps/ai_assistant/models.py` | 修改 | system_prompt 默认值清空（改由 factory 动态注入）|

---

## 五、实施顺序

```
阶段一（Harness Engineering — 30分钟）
  ① 修改 device_tools.py      → get_online_devices 触发式描述
  ② 修改 case_tools.py       → list_test_cases 触发式描述
  ③ 修改 runner_tools.py      → run_test 触发式描述
  ④ 修改 agent_factory.py    → 动态注入平台上下文提示词
  ⑤ 重启 AgentScope           → 生效

阶段二（Loop Engineering 基础 — 30分钟）
  ⑥ 新建 tools/base.py        → 工具日志基类
  ⑦ 修改 factory.py           → 添加 PlatformCapabilitiesTool
  ⑧ 配置 AIAgent.memory_mode → longterm（需 AgentScope 支持）

阶段三（自动化 Loop — 60分钟）
  ⑨ 新建 loops/device_monitor.py → 设备监控循环
  ⑩ 配置 WorkBuddy 自动化        → 定时报告推送
```

---

## 六、验证方法

修改完成后，测试以下场景：

| 测试用例 | 预期行为 |
|----------|---------|
| "当前有几台设备？" | LLM 调用 `get_online_devices` → 返回实时设备列表 |
| "有哪些测试用例？" | LLM 调用 `list_test_cases` → 返回用例清单 |
| "帮我执行 smoke 测试" | LLM 调用 `get_online_devices` → `acquire_device` → `run_test` |
| "你能做什么？" | LLM 调用 `list_platform_capabilities` → 返回完整能力清单 |
| 对话历史跨页面刷新后保留 | `memory_mode='longterm'` → 历史不丢失 |
| 工具调用记录到数据库 | `AIExecutionLog` 中出现 `[TOOL CALL]` 日志 |

---

## 七、关键技术参考

```
AgentScope 2.0 源码位置:
  C:/Users/zhiyan/AppData/Roaming/Python/Python313/site-packages/agentscope/

关键模块:
  agentscope/app/_toolkit.py     → get_toolkit() 构建方式
  agentscope/app/_service/_chat.py → chat_with_agent() 流式对话
  agentscope/app/_lifespan.py    → Redis / DB 初始化
  agentscope/memory/             → MemoryWithRDBMS 持久化记忆

AgentScope 2.0 Agent 核心字段:
  Agent(name, system_prompt, model, toolkit, memory,
        max_iters, parallel_tool_calls, ...)
```
