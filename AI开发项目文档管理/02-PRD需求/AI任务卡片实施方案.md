# AI 智能体任务卡片完整实施方案

> 基于 AgentScope 官方文档（消息与事件 / 模型 / 上下文管理 / 工具 / 计划模式 / 中间件 / 长期记忆）深度分析，结合平台现状，2026-07-02

---

## 一、现状分析

### 1.1 能力矩阵（AgentScope 7 大模块 × 平台实现）

| 模块 | AgentScope 能力 | 平台现状 | 优先级 |
|------|----------------|---------|--------|
| 消息与事件 | ContentBlock / HintBlock / REPLY_* / THINKING_* / TOOL_* | ✅ SSE 流处理 + ContentBlock 持久化 | P2 |
| 模型 | DashScope / OpenAI / DeepSeek / structured output | ✅ 多 Provider + structured fallback | — |
| 上下文管理 | AgentState / StateStore (Redis/MySQL) / RuntimeContext | ⚠️ 单会话持久化，**跨会话断裂** | P1 |
| 工具系统 | 17 个业务工具 + MCP + 外部执行 | ✅ 工具齐全，但**缺少任务管理工具** | P1 |
| **计划模式** | ReAct / hint 标签 / max_iters | ❌ **未启用**，AI 不会主动拆解任务 | **P0** |
| 中间件 | 5 Hook (onAgent/onReasoning/onActing/onModelCall/onSystemPrompt) | ❌ **未使用**，无任务生命周期追踪 | P1 |
| 长期记忆 | Mem0LongTermMemory / agent_control / static_control | ⚠️ 配置存在但**未实际启用** | P1 |

### 1.2 用户目标的差距

**用户期望**：
> "通过对话 AI 会自己创建任务，输出任务卡片在 AI 对话窗可以查看历史记录，创建完卡片后开始执行任务。"

**当前实际**：
1. `create_runner_task` 工具存在，但只返回纯文本结果
2. AI 不知道何时应该创建任务（计划模式未启用）
3. 没有任务卡片 UI 渲染
4. 无历史任务卡片查看区域
5. 无法追踪任务执行状态（无中间件钩子）

---

## 二、目标架构

### 2.1 端到端工作流

```
用户对话 → 意图识别 → ReAct 计划推理
    ↓
create_runner_task 工具调用（写入 TestRunRecord）
    ↓
SSE 流返回 → HintBlock(task_card) → 前端渲染任务卡片
    ↓
任务执行（run_test 工具）→ 执行管道（acquire → run_test → release）
    ↓
REPLY_END → 卡片状态更新为 COMPLETED/FAILED
    ↓
历史任务卡片区域（对话内可见）
```

### 2.2 三大核心组件

| 组件 | 职责 | 关键技术 |
|------|------|---------|
| **任务计划层** | AI 识别测试意图，主动拆解任务步骤 | `hint` 标签计划引导 + 系统提示词增强 |
| **任务卡片层** | 在对话中渲染可交互任务卡片 | `HintBlock{hint="task_card"}` + SSE 实时状态推送 |
| **任务执行层** | 执行测试用例并回写结果 | `run_test` 工具 + TestRunRecord + SSE 执行状态事件 |

---

## 三、实施路线图

```
阶段一（P0）│ 任务卡片 UI 渲染 — 让 AI 对话能显示任务卡片
阶段二（P0）│ 计划模式启用 — AI 主动拆解任务步骤（hint 标签）
阶段三（P1）│ 任务管理工具集 — list_tasks / update_task / save_test_case
阶段四（P1）│ 历史任务面板 — 对话内查看/管理所有任务卡片
阶段五（P1）│ 中间件任务追踪 — 全生命周期 Hook
阶段六（P1）│ 长期记忆集成 — agent_control 模式跨会话记忆
```

---

## 四、阶段一：任务卡片 UI 渲染（P0）

### 4.1 核心技术思路

AgentScope SSE 事件流中 `HintBlock` 的 `hint` 字段可以携带 JSON 结构化数据。前端解析 `hint` 字段，当 `hint.type === 'task_card'` 时，渲染成可交互的任务卡片。

**不需要修改 AgentScope 源码**，只需：
1. 增强 `create_runner_task` 工具的返回（加入 HintBlock）
2. 前端解析 HintBlock 并渲染

### 4.2 HintBlock 格式设计

AgentScope `HintBlock` 格式：
```json
{
  "type": "hint",
  "id": "task-card-001",
  "hint": {
    "type": "task_card",
    "task_id": "ai-task-7f3a2c",
    "title": "Smoke Test - 登录流程",
    "status": "RUNNING",
    "device": "RF8N21MSW7A",
    "cases": ["c001", "c002", "c003"],
    "case_titles": ["登录页面验证", "点击登录按钮", "断言登录成功"],
    "loop_count": 1,
    "run_id": "ai-task-7f3a2c",
    "progress": { "current": 1, "total": 3 },
    "actions": ["view_detail", "stop", "rerun"]
  }
}
```

### 4.3 代码改动

#### 4.3.1 增强 `create_runner_task` 工具（task_tools.py）

```python
from agentscope.message import TextBlock, HintBlock, ToolChunk

async def call(self, task_name, device_serial, case_ids, loop_count=1, start_immediately=False, **kwargs):
    # ... 现有逻辑不变 ...

    # 新增：返回 HintBlock，触发前端渲染任务卡片
    return ToolChunk(content=[
        TextBlock(text=result),  # 保留原有文本返回
        HintBlock(
            id=f"task-card-{run_id}",
            hint={
                "type": "task_card",
                "task_id": run_id,
                "title": task_name,
                "status": "PENDING",
                "device": device_serial,
                "device_model": device.model or device.name,
                "cases": case_ids,
                "case_titles": [get_definition(cid).title for cid in case_ids],
                "loop_count": loop_count,
                "run_id": run_id,
                "progress": {"current": 0, "total": len(case_ids) * loop_count},
                "actions": ["view_detail", "start", "delete"],
            }
        )
    ])
```

#### 4.3.2 前端 api.js — 添加 HintBlock 回调

```javascript
// SSEMessageBuilder 中 dispatchUIEvent
if (phase === 'hint_delta') {
  callbacks.onHintDelta?.(uiEvent.hint, uiEvent.hint_id)
  return
}
// Hint end — 完整 hint block
if (phase === 'hint_end') {
  callbacks.onHintEnd?.(uiEvent.hint, uiEvent.hint_id)
  return
}
```

#### 4.3.3 前端 ChatView.vue — 任务卡片渲染

```vue
<!-- 消息气泡内的任务卡片 -->
<div v-if="m.hint && m.hint.type === 'task_card'" class="task-card">
  <div class="task-card-header">
    <span class="task-status-badge" :class="statusClass">{{ m.hint.status }}</span>
    <span class="task-id">#{{ m.hint.task_id }}</span>
  </div>
  <div class="task-title">{{ m.hint.title }}</div>
  <div class="task-meta">
    设备: {{ m.hint.device }} ({{ m.hint.device_model }})<br>
    用例: {{ m.hint.cases.length }}个 | 循环: {{ m.hint.loop_count }}
  </div>
  <div class="task-cases">
    <div v-for="(title, i) in m.hint.case_titles" :key="i" class="case-item">
      {{ i+1 }}. {{ title }}
    </div>
  </div>
  <!-- 进度条 -->
  <div v-if="m.hint.progress" class="progress-bar">
    <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
  </div>
  <!-- 操作按钮 -->
  <div class="task-actions">
    <button @click="viewTaskDetail(m.hint.run_id)">查看详情</button>
    <button v-if="m.hint.status === 'PENDING'" @click="startTask(m.hint.run_id)">启动</button>
    <button v-if="m.hint.status === 'RUNNING'" @click="stopTask(m.hint.run_id)">停止</button>
  </div>
</div>
```

### 4.4 任务卡片 CSS

```css
.task-card {
  margin: 8px 0;
  border: 1.5px solid #534AB7;
  border-radius: 10px;
  padding: 12px 14px;
  background: #FAF9F6;
  max-width: 420px;
}
.task-card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.task-status-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 700;
}
.task-status-badge.PENDING { background: #E6F1FB; color: #185FA5; }
.task-status-badge.RUNNING { background: #FAEEDA; color: #BA7517; animation: blink 1s infinite; }
.task-status-badge.COMPLETED { background: #EAF3DE; color: #3B6D11; }
.task-status-badge.FAILED { background: #FCEBEB; color: #A32D2D; }
.task-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.task-meta { font-size: 12px; color: #444441; margin-bottom: 8px; }
.case-item { font-size: 12px; color: #666; padding: 2px 0; border-bottom: 1px solid #f0ede8; }
.progress-bar { height: 4px; background: #e8e6e0; border-radius: 2px; margin: 8px 0; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #7F77DD, #534AB7); transition: width 0.3s; }
.task-actions { display: flex; gap: 8px; margin-top: 8px; }
.task-actions button { flex: 1; padding: 4px 8px; border-radius: 6px; font-size: 12px; cursor: pointer; }
```

---

## 五、阶段二：计划模式启用（P0）

### 5.1 核心原理

AgentScope 支持通过 `hint` 标签在 System Prompt 中指示 AI 在特定时机插入 `<system-hint>` 消息，引导后续推理方向。

**`hint` 标签系统**：
- `<system-hint type="plan">先创建测试计划</system-hint>` → AI 推理前先规划
- `<system-hint type="task_create">创建任务卡片</system-hint>` → AI 调用 `create_runner_task`
- `<system-hint type="execute">开始执行</system-hint>` → AI 调用 `run_test`

### 5.2 系统提示词增强

在 `agent_factory.py` 的 `_PLATFORM_CONTEXT` 中添加计划引导段：

```python
_TASK_PLANNING_HINT = """
## 任务计划模式

当用户提出以下类型的请求时，你**必须**先创建任务计划（hint标签），再逐步执行：

1. **测试执行类**：用户说"执行测试"、"跑一下"、"测试这些用例"
   → 先调用 `create_runner_task` 创建任务卡片（立即显示给用户）
   → 再调用 `acquire_device` 锁定设备
   → 再调用 `run_test` 开始执行
   → 执行完成后调用 `release_device` 释放设备

2. **测试创建类**：用户说"帮我写用例"、"创建一个测试"
   → 先调用 `list_test_cases` 查看现有用例
   → 再调用 `save_test_case` 创建新用例
   → 用例创建完成后，询问用户是否执行

3. **探索类**：用户说"看看"、"查询"、"有多少"
   → 直接调用对应工具获取实时数据
   → 回答简洁，基于数据

## Hint 标签使用规范

在回复中使用 `<system-hint>` 标签标记关键阶段：

- `<system-hint type="plan">检查设备 → 查询用例 → 创建任务 → 执行 → 释放设备</system-hint>`
- `<system-hint type="task_created">任务卡片已显示，用户可以查看详情</system-hint>`
- `<system-hint type="executing">正在执行第 N/总M 个用例...</system-hint>`
- `<system-hint type="done">测试完成，通过N个，失败M个</system-hint>`

这些 hint 标签会被渲染成可视化的任务卡片，用户可以在对话中实时追踪执行进度。
"""
```

### 5.3 计划触发条件（系统提示词注入）

在 `_build_system_prompt()` 中，对"测试执行"类请求自动注入计划引导：

```python
def _build_system_prompt(db_agent):
    # 基础平台上下文（已有）
    base = _PLATFORM_CONTEXT

    # 检查是否需要注入计划引导
    # 通过 AIAgent 模型中的 memory_mode / agent_mode 字段控制
    planning_hint = ""
    if db_agent.memory_mode == "planning":
        planning_hint = _TASK_PLANNING_HINT

    # 合并
    user_specific = db_agent.system_prompt or ""
    return f"{base}\n{planning_hint}\n{user_specific}".strip()
```

---

## 六、阶段三：任务管理工具集（P1）

新增 3 个任务管理工具，完整覆盖任务生命周期：

### 6.1 `list_ai_tasks` — 列出历史任务

```python
class ListAITasksTool(ToolBase):
    name = "list_ai_tasks"
    description = """列出 AI 创建的任务卡片历史。

何时使用：
- 用户问"我创建了哪些任务"、"查看历史任务"
- 用户问"上次测试结果是什么"
- 用户想继续之前未完成的任务

返回：任务名称、状态、执行时间、结果摘要。"""
    input_schema = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["pending", "running", "completed", "failed", "all"],
                "description": "按状态过滤（默认 all）"
            },
            "limit": {"type": "integer", "description": "最多返回数量（默认 20）"}
        }
    }
    # 返回 TestRunRecord 的任务列表
```

### 6.2 `update_ai_task` — 更新任务状态

```python
class UpdateAITaskTool(ToolBase):
    name = "update_ai_task"
    description = """更新 AI 任务的状态（内部使用，由执行管道自动调用）。
通常不需要直接调用。"""
    input_schema = {
        "type": "object",
        "properties": {
            "run_id": {"type": "string", "description": "任务 run_id"},
            "status": {"type": "string", "enum": ["RUNNING", "COMPLETED", "FAILED"]},
            "progress": {"type": "object", "description": "进度 {current, total}"},
        }
    }
```

### 6.3 增强 `create_runner_task` — 加入 HintBlock

见阶段一 4.3.1。

---

## 七、阶段四：历史任务面板（P1）

在 AI 对话窗口右侧/底部新增历史任务面板：

```
┌─────────────────────────────┐
│  历史任务卡片               │
├─────────────────────────────┤
│  ● Smoke Test 登录  [COMPLETED] │
│    #ai-task-7f3a | 14:32  │
├─────────────────────────────┤
│  ✗ 回归测试 支付    [FAILED]    │
│    #ai-task-2c9b | 14:20  │
├─────────────────────────────┤
│  ○ 新建: 搜索功能   [PENDING]   │
│    #ai-task-a1b2 | 14:35  │
└─────────────────────────────┘
```

实现方式：
1. 在 `ChatView.vue` 中新增 `taskHistory` ref 数组
2. 当 `onHintEnd` 收到 `type === 'task_card'` 时，追加到 `taskHistory`
3. 提供 `viewTaskDetail(run_id)` 跳转查看详情
4. 提供 `loadTaskHistory()` 在 `selectChat` 时从 Django API 加载

Django API：
```python
# GET /api/ai/conversations/{id}/tasks
def list_conv_tasks(request, conv_id):
    tasks = TestRunRecord.objects.filter(
        run_id__startswith='ai-task-'
    ).order_by('-started_at')[:20]
    return JsonResponse({"ok": True, "tasks": [
        {"run_id": t.run_id, "status": t.status,
         "device": t.device_serial, "cases": t.selected_cases,
         "summary": t.summary, "started_at": t.started_at}
        for t in tasks
    ]})
```

---

## 八、阶段五：中间件任务追踪（P1）

在 `agent_factory.py` 中注册中间件，追踪任务生命周期：

```python
from agentscope_service.middleware import TaskLifecycleMiddleware

class TaskLifecycleMiddleware(MiddlewareBase):
    """追踪 AI 任务生命周期的中间件。"""

    def __init__(self, user_id, conversation_id):
        self.user_id = user_id
        self.conversation_id = conversation_id

    async def onActing(self, agent, ActingInput input, next_fn):
        """每次工具调用前后记录日志。"""
        tool_name = input.toolCalls[0].name if input.toolCalls else "?"
        await self._log(f"[acting] tool={tool_name} args={input.toolCalls[0].arguments}")

        result = await next_fn(input)

        # 工具执行完成，检查是否创建了任务
        if tool_name == "create_runner_task":
            await self._notify_task_created(input)
        elif tool_name == "run_test":
            await self._notify_task_started(input)

        return result

    async def onAgent(self, agent, AgentInput input, next_fn):
        """每次 reply 前后记录。"""
        await self._log(f"[agent] msgs_count={len(input.msgs)}")
        return await next_fn(input)

    async def _log(self, message):
        AIExecutionLog.objects.create(
            agent_id=self.agent_id,
            conversation_id=self.conversation_id,
            level="info",
            message=message,
        )
```

注册到 AgentScope：
```python
# agent_factory.py
def build_agent_from_db(agent_id, user_id):
    # ...
    middlewares = [TaskLifecycleMiddleware(user_id, conversation_id)]
    agent = ReActAgent(
        # ...
        middlewares=middlewares,
    )
```

---

## 九、阶段六：长期记忆集成（P1）

利用 AgentScope 的 `Mem0LongTermMemory` / `ReMePersonalLongTermMemory` 实现跨会话记忆：

### 9.1 架构设计

```
┌──────────────────────────────────────────────┐
│              AgentScope                       │
│  ┌────────────────────────────────────────┐ │
│  │  InMemoryMemory (短期上下文)             │ │
│  └────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────┐ │
│  │  Mem0LongTermMemory (长期记忆)          │ │
│  │  agent_control 模式 → 自动 record/retrieve│ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
         ↓ persist              ↓ semantic search
┌──────────────────────────────────────────────┐
│  MySQL (android_autotests)                  │
│  ai_conversations / ai_messages / ai_tasks   │
│  + Embedding 向量存储（Mem0 后端）           │
└──────────────────────────────────────────────┘
```

### 9.2 实现方案

AgentScope 的 `Mem0LongTermMemory` 需要：
- LLM（用于摘要和检索）
- Embedding 模型（用于向量存储）
- 向量数据库后端（支持 MySQL）

**推荐配置**（平台已有 MySQL 8.4.4）：
```python
# agentscope_service/memory.py
from agentscope.memory import Mem0LongTermMemory

long_term_memory = Mem0LongTermMemory(
    agent_name="TestAssistant",
    user_name=str(user_id),
    model=DashScopeChatModel(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model_name="qwen-max-latest",
    ),
    embedding_model=DashScopeTextEmbedding(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        model_name="text-embedding-v3",
    ),
    # 使用 MySQL 作为向量存储后端
    backend="mysql",
    connection_params={
        "host": "127.0.0.1",
        "user": "root",
        "password": "autotests2026",
        "database": "android_autotests_mem0",
    },
)
```

**Django 中注册长期记忆**（agent_factory.py）：
```python
def build_agent_from_db(agent_id, user_id):
    db_agent = AIAgent.objects.get(id=agent_id)

    # 根据 memory_mode 决定是否启用长期记忆
    if db_agent.memory_mode in ("longterm", "both"):
        from agentscope_service.memory import build_long_term_memory
        long_term_memory = build_long_term_memory(user_id)
        long_term_memory_mode = db_agent.long_term_memory_mode or "both"
    else:
        long_term_memory = None
        long_term_memory_mode = None

    agent = ReActAgent(
        # ...
        long_term_memory=long_term_memory,
        long_term_memory_mode=long_term_memory_mode,
    )
```

### 9.3 长期记忆的内容策略

| 内容 | 记录时机 | 检索时机 |
|------|---------|---------|
| 用户偏好 | 首次使用平台时 | 每次对话开始 |
| 历史任务摘要 | `create_runner_task` 后 | 用户问"上次测试结果" |
| 用例创建记录 | `save_test_case` 后 | 用户想继续编写用例 |
| 失败案例分析 | `run_test` FAILED 后 | 用户问"上次为什么失败" |

---

## 十、实施优先级与工作量

| 阶段 | 改动 | 工作量 | 收益 |
|------|------|--------|------|
| **阶段一** | `task_tools.py` HintBlock + ChatView.vue 卡片渲染 | 中 | 立即可见效果 |
| **阶段二** | `agent_factory.py` 计划提示词 | 小 | AI 主动拆解任务 |
| **阶段三** | 新增 2 个任务管理工具 | 中 | 完整任务生命周期 |
| **阶段四** | 历史任务面板 + Django API | 中 | 任务历史可追溯 |
| **阶段五** | 中间件注册 | 中 | 全链路可观测 |
| **阶段六** | Mem0 集成 | 大 | 跨会话记忆 |

**建议实施顺序**：阶段一 → 阶段二 → 阶段三 → 阶段四 → 阶段五 → 阶段六

---

## 十一、验证方法

### 阶段一验证
1. 对 AI 说："帮我对登录流程做个冒烟测试"
2. 预期：在对话气泡中看到紫色边框的任务卡片（含设备/用例/状态）
3. 卡片上有"启动"按钮

### 阶段二验证
1. 对 AI 说："执行所有回归测试用例"
2. 预期：AI 先返回计划 hint（显示步骤列表），然后逐步调用工具
3. 每次工具调用在气泡中显示进度

### 阶段四验证
1. 在对话中创建多个任务
2. 下拉滚动条，底部显示历史任务面板
3. 点击"查看详情"，跳转测试执行页面
