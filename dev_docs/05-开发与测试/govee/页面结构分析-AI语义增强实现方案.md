# 页面结构分析 — AI 语义增强实现方案（基于 AgentScope 2.0.3）

> 日期：2026-08-25 · 前置：纯规则结构分析已上线（`algorithms/layout.py` + `GET /snapshots/{id}/analyze`）
> 本文：在纯规则之上新增 **LLM 语义增强层**，只在 AI 助手对话入口触发，前端按钮保持纯规则。

---

## ⚠️ 重要修正（2026-08-25，真实 LLM 验证后）

原方案用 `generate_structured_output`（强制 tool_choice）做语义抽取，但**真实调用暴露了 thinking 模式模型（如 `deepseek-v4-flash-vision-exp`）不支持强制 tool_choice**（`400 Thinking mode does not support this tool_choice`），导致结构化输出不稳定。

修正为**复用平台既有的「工具入参 + handler 校验」模式**（对齐 `save_case` 的 `steps`/`config_json`）：

- **不用 `generate_structured_output`**，改由 Agent 的 ReAct 循环**自然产生**语义命名（`tool_choice='auto'`，thinking 支持）。
- **拆两个工具**：
  1. `analyze_page`（read_only）→ 纯规则分区，返回元素，**无 LLM**。
  2. `save_page_semantic`（write）→ 语义命名作为工具入参（page_summary + elements[{resource_id, func_name}] + cards），handler 校验（rid 必须在快照元素集合内 + metrics 枚举）。
- **移除 model 透传**（agent_factory/in_process_tool 不再透传 model）。
- **`llm_semantic.py` 改纯校验模块**：`validate_semantic()`（rid 真实性 + metrics 枚举 + 结构清洗），不再调 LLM。

> 下文 §2/§3/§4 为原始方案，以本「修正」为准；openspec 的 design.md/specs 已按修正更新。

---

## 0. AgentScope 2.0.3 调研结论（关键机制）

| 问题 | 结论 |
| --- | --- |
| 单次模型调用 API | `model.generate_structured_output(messages, structured_model)`（`async`） |
| 结构化输出支持 | ✅ **原生内置**：`structured_model` 传 **Pydantic 模型类**或 JSON Schema dict |
| JSON 合法性保证 | AgentScope 内部**强制 tool_choice 调 `generate_structured_output` 工具 + 自动 jsonschema/Pydantic 校验** |
| 消息格式 | `SystemMsg(name="system", content=str)` + `UserMsg(name="user", content=str)`（str 自动转 TextBlock） |
| tool handler 是 sync 还是 async | **sync**（`InProcessPlatformTool.call()` 里 `asyncio.to_thread(handler, ...)` 跑在线程池） |
| model 是否持有跨循环 async 资源 | ❌ **不持有**。`_call_api` 每次 `openai.AsyncClient(...)` 新建 client（OpenAI/DashScope 均如此），model 是无状态配置容器 |

**核心结论**：
1. 不用手写 function calling / json_schema / jsonschema 校验——`generate_structured_output` 全包了。
2. **复用 Agent 的 model 实例是安全的**：model 只是 `{credential, model名, parameters}` 配置容器，每次调用自建 client 绑定当前 loop，无跨线程复用资源隐患。

---

## 1. 组件落位

```
apps/ai_assistant/agent_scope/
├── llm_semantic.py          # 新增：Pydantic 输出模型 + extract()（同步入口，内部 asyncio.run）
├── tool_registry.py         # 修改：新增 analyze_page 工具 schema + handler（含 _model 形参）
├── in_process_tool.py       # 修改：InProcessPlatformTool 持 model + call() 时注入
└── agent_factory.py         # 修改：_build_toolkit 透传 model

algorithms/layout.py         # 复用：classify_structure（纯规则骨架）
apps/device_inspector/api.py # 复用：capture_snapshot / analyze_snapshot
```

---

## 2. `llm_semantic.py` 设计（核心）

### 2.1 Pydantic 输出模型（AgentScope 直接用它做约束 + 校验）

```python
from pydantic import BaseModel, Field
from typing import Literal

class SemanticElement(BaseModel):
    resource_id: str
    func_name: str                       # 功能名：网关入口/开关/设备名
    metrics: list[Literal["可点击", "可滚动", "可勾选"]] = Field(default_factory=list)

class SemanticSection(BaseModel):
    name: str
    role: Literal["status_bar","header","tab_bar","content","bottom_nav","system_nav","other"]
    element_ids: list[str] = Field(default_factory=list)

class SemanticCard(BaseModel):
    name: str
    fields: dict = Field(default_factory=dict)

class PageSemantic(BaseModel):
    page_summary: str
    sections: list[SemanticSection] = Field(default_factory=list)
    elements: list[SemanticElement]
    cards: list[SemanticCard] = Field(default_factory=list)
```

> 用 **Pydantic 模型**（而非 JSON Schema dict）：`generate_structured_output` 直接 `model_validate`，类型安全 + 校验一体。

### 2.2 `extract()` 同步入口（内部桥接 async）

```python
def extract(model, elements, package, activity) -> dict:
    """LLM 语义抽取。同步入口（handler 在线程中调用），内部 asyncio.run 桥接。"""
    input_rids = {e["resource_id"] for e in elements if e.get("resource_id")}
    messages = [
        SystemMsg(name="system", content=SYSTEM_PROMPT),     # 指令 + few-shot
        UserMsg(name="user", content=json.dumps({"package": package, "elements": elements}, ensure_ascii=False)),
    ]

    async def _run():
        resp = await model.generate_structured_output(messages, PageSemantic)
        return resp.content  # 已通过 Pydantic 校验的 dict

    try:
        raw = asyncio.run(_run())
    except Exception:
        return _fallback(elements)   # 降级纯规则：func_name 回退 class 短名

    # 语义约束（AgentScope 校验管不了）：resource_id 必须在输入集合内，防幻觉
    for el in raw.get("elements", []):
        if el["resource_id"] not in input_rids:
            el["func_name"] = ""     # 编造的 rid 丢弃语义命名
    return raw
```

### 2.3 Prompt（system + few-shot）

```
SYSTEM_PROMPT = """
你是 UI 层级语义抽取器。输入是 Android 页面元素列表（JSON）。
任务：1) 给每个 resource_id 起中文功能名（ivGateway→网关入口）；2) 识别页面分区；
3) 识别重复卡片结构（设备名/状态/开关/连接图标）；4) 用一句话总结页面意图。
硬约束：只能解释输入中已存在的 resource_id/text，禁止发明不存在的元素。
"""
```

---

## 3. model 透传链路（3 处小改）

### 3.1 `agent_factory.py`

```python
def build_agent(...):
    model = _build_model(...)                        # 已有
    toolkit = _build_toolkit(agent_model, user_id, model)   # 新增 model 参数
```

### 3.2 `in_process_tool.py`

```python
class InProcessPlatformTool(ToolBase):
    def __init__(self, ..., model=None):
        self._model = model

    async def call(self, **kwargs):
        params = {k: v for k, v in kwargs.items() if k not in ("user_id",)}
        if self._config["name"] == "analyze_page":
            params["_model"] = self._model          # 注入 model
        result = await asyncio.to_thread(handler, self._user_id, **params)
```

### 3.3 `tool_registry.py`

```python
@_register("inspector", "analyze")
def _inspector_analyze(user_id, serial=PROTECTED, snapshot_id=None, _model=None, **kwargs):
    if serial is PROTECTED and not snapshot_id:
        raise ValueError("缺少必填参数: serial 或 snapshot_id")
    from apps.device_inspector.api import capture_snapshot, analyze_snapshot
    from .llm_semantic import extract

    # 1) 取快照（已有快照优先，否则 capture）
    data = analyze_snapshot(snapshot_id) if snapshot_id else _capture_and_analyze(user_id, serial)

    # 2) LLM 语义（_model 存在才做，否则纯规则）
    if _model is not None:
        semantic = extract(_model, data["elements"], data["package"], data["activity"])
        data["page_summary"] = semantic.get("page_summary", "")
        data["cards"] = semantic.get("cards", [])
        _apply_func_names(data["elements"], semantic.get("elements", []))
    return data
```

---

## 4. `analyze_page` 工具 schema（tool_registry.py 的 TOOL_SCHEMAS 新增）

```python
{
    "name": "analyze_page",
    "category": "设备检查器",
    "icon": "📸",
    "summary": "抓取并分析页面结构：6层分区 + 元素功能名 + XPath + 页面意图（LLM 语义增强，失败降级纯规则）",
    "module": "inspector",
    "action": "analyze",
    "params": [
        {"name": "serial", "type": "string", "required": False, "desc": "设备序列号"},
        {"name": "snapshot_id", "type": "integer", "required": False, "desc": "已有快照ID（与 serial 二选一，优先 snapshot_id）"},
    ],
    "read_only": True,
}
```

---

## 5. 数据流转

```
用户「分析这个页面」
  → Agent(ReAct) 调 analyze_page(serial)
  → InProcessPlatformTool.call()（async）→ asyncio.to_thread(handler)（线程）
      → handler: capture → classify_structure（规则）
      → extract(model, ...)（sync，内部 asyncio.run 桥接 generate_structured_output）
      → 合并规则 + 语义 → 返回 dict
  → _format_result → ToolChunk → Agent 自然语言汇报
```

---

## 6. 降级链（三层，全部兜底到纯规则）

```
generate_structured_output（AgentScope 强制 tool + Pydantic 校验）
  → 失败（API 异常/校验失败）→ extract 捕获 → _fallback 纯规则
  → 语义约束（rid 必须真实存在）→ 非法 rid 的 func_name 置空
  → _model 为 None（未透传）→ 直接纯规则
```

---

## 7. 复用 Agent model 实例的理由（源码验证）

1. AgentScope model 是**无状态配置容器**：`{credential, model名, parameters(temperature/max_tokens/...), stream}`。
2. `_call_api` 每次调用 **`openai.AsyncClient(...)` 新建 client**（OpenAI/DashScope 源码一致），绑定当前事件循环，用完即弃，无跨 loop 资源。
3. 复用 = 传引用零成本，且保证用用户配置的**同一个 model**；重建 = 拆散 config 再拼一遍，多一次 `decrypt_key + _build_model`，还要手动保证 config 一致。
4. 唯一要做的不是"要不要复用"，而是"怎么把 model 安全送到 handler"——纯引用透传（agent_factory → _build_toolkit → build_platform_tools → InProcessPlatformTool → call 注入）。

---

## 8. 分阶段

| 阶段 | 内容 | 验证 |
| --- | --- | --- |
| **P0** | `llm_semantic.py`：PageSemantic Pydantic + extract + _fallback | 用**假 model**（返回固定 dict）单测：正常/降级/幻觉 |
| **P1** | model 透传（agent_factory → in_process_tool → handler） | 单测验证 model 注入链路 |
| **P2** | `analyze_page` schema + handler + 注册 | 工具在 Agent 对话可调 |
| **P3**（缓做） | 命名缓存/沉淀 | 同 App 二次不调 LLM |

---

## 9. 与初版方案的差异（AgentScope 调研带来的简化）

1. ❌ 删掉手写 function calling / json_schema / jsonschema 校验 → **用 `generate_structured_output` + Pydantic 内置**；
2. ✅ 单次调用 API 确定为 `generate_structured_output`（async）；
3. ✅ 桥接方式确定为 handler 内 `asyncio.run()`（因为 handler 在线程池里）；
4. ✅ 复用 model 实例的安全性由源码证明（无跨 loop 资源），不再是"需实测风险"。

---

## 10. 范围外（明确不做）

- ❌ 前端按钮仍走纯规则（不改 device_inspector 已上线代码）
- ❌ 不新增 WS/SSE
- ❌ 命名缓存 P3 本次缓做（避免过度设计）
