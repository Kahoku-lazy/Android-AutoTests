# ae_harness/tools · 域工具与目录准入
> 归属模块：`engines/ae_harness/tools` ｜ 类型：引擎模块开发说明
> 代码真相源：`engines/ae_harness/tools/catalog.py`、`engines/ae_harness/tools/adb/tools.py`
> 上级约束：engines/AGENTS.md ｜ 模块索引：engines/AGENTS.md

## 职责

本目录为 Agent 提供工具（tools）。

当前只做 **Python 内置函数工具**：用 `agentscope.tool.FunctionTool` 包装普通 Python 函数，按域分子目录。

```text
tools/
  catalog.py       只读目录：域、预设、函数名与一句说明；不含实现
  adb/             设备操作 + build_adb_tools / build_adb_readonly_tools
  case_library/    保存用例；写入函数由调用方注入
  document/        读取调用方绑定的文档正文
  scripted/        按名字与入参形状回放文本；剧本由调用方传入
```

`list_tool_catalog()` 只给配置页下拉用。勾选过滤在 `backend_bridge`，不在本目录。

工具不属于角色三要素，`create_agent` 不接收。调用方先建 Agent，再挂工具：

```python
agent = create_agent(
    name,
    system_prompt=system_prompt,
    provider="openai",
    api_key_env="OPENAI_API_KEY",
    model_name="deepseek-flash",
).agent
for tool in build_adb_tools():
    await agent.toolkit.add_tool(tool)
```

## 红线（AI 禁止事项）

1. **禁止在本目录创建 Agent 或造模型** —— 不调 `Agent(...)`、不构造 `DeepSeekChatModel` 之类的客户端。
2. **禁止在本目录读配置文件** —— 不 `import yaml`、不 `open()`、不读 `.env`；需要配置由调用方传入。
3. **禁止在本目录发起回复** —— 不调 `reply` / `reply_stream`，工具只执行动作并返回结果。
4. **禁止引入 MCP、Skill、外部执行工具** —— 当前只做 Python 函数工具；需要这些能力先上报，不要自行扩展。
5. **禁止反向依赖 `agents/`** —— 工具不知道 Agent 存在，两者只在调用方汇合。
6. **禁止工具之间互相调用来做编排** —— 每个工具只做一个动作；多步流程由 Agent 决策，不写进工具。
7. **禁止改变返回结构的契约** —— `status`、`timestamp` 字段缺一不可，字段含义不得改名或复用。
8. **禁止接受像素坐标** —— 参数只收归一化值，换算在工具内部完成。
9. **禁止把工具文件堆在 `tools/` 根上** —— 新工具必须放进对应域的子目录。
10. **目录准入门禁** —— 本目录只允许三种形态：**Python 内置函数工具**、**Skill**、**MCP**。自带配置、向量库或索引状态的模块（例如知识库）**不接受**，一律放 Harness 根级子包（知识库见 [`ae_harness_knowledge_kb_retrieval.md`](../ae_harness_knowledge/ae_harness_knowledge_kb_retrieval.md)）。

## 实现约定

1. **文本类工具返回 JSON 文本** —— 成功带 `timestamp`、`status: true` 与载荷字段；失败带 `timestamp`、`status: false` 与 `error`。时间戳格式固定为 `2026-11-13_10-53-12.321`（毫秒三位）。
2. **截图返回图片块** —— `adb_screenshot` 返回 `ToolChunk`：一段 JSON 元信息 + `DataBlock`（PNG 的 base64）。`with_timing=True`（默认）时带 `cost_ms`；传 `marks` 时在图上画红圈加序号。
3. **网格核对** —— `adb_screenshot_grid(nx, ny, size=3, step=0.03)` 以粗估点为中心撒网格，候选点画成十字加序号，元信息回传序号与坐标。3×3 可读；5×5 在 1568 长边下序号会糊成一团，**优先用两轮 3×3**（第二轮步长 0.012）。
4. **只读与并发标记** —— 只读工具标 `is_read_only=True`，有副作用的标 `is_concurrency_safe=False`。
5. **坐标一律归一化** —— 0~1，左上角 `(0,0)`，右下角 `(1,1)`，执行时按 `wm size` 换算。
6. **截图不落盘** —— 只以 base64 随结果返回，长边压到 1568 以内，不写任何文件。

## 已知限制

### 视觉定位精度

坐标用归一化值，换算本身不损失精度（4 位小数在 1440 宽屏上小于 1 像素）。真正的误差来自模型看图的视觉估计，实测为 **0.03~0.08 归一化值**。

| 控件尺寸 | 归一化宽度 | 结果 |
| --- | --- | --- |
| ≥ 150 px | ≥ 0.10 | 可点中 |
| 60 ~ 150 px | 0.04 ~ 0.10 | 有风险，必须走网格核对 |
| < 60 px | < 0.04 | 不可靠，先换等价大目标 |

实测（1440×3040 天气页）：居中的「更多」按钮纵向偏 90 px，右上角「+」偏 237 px，底部方框键只偏 17 px。
