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
3. **环点阵核对** —— `adb_screenshot_grid(nx, ny, size=3, step=0.03, marker="ring", step_y=0)` 以粗估点为中心撒点阵，元信息回传每个候选点的序号、行号、列号与归一化坐标。标记形态只有一种：
   - `marker="ring"`（缺省）：空心圆环，行列号标在点阵外沿（列号在首行上方、行号在首列左侧），目标从环心透出。小控件用 5×5 或 7×7，两轴步长按目标尺寸收窄。
   - `marker="cross"` 已废弃，收到时按 `ring` 渲染，仅为旧提示词/旧任务保留兼容。
   `step_y=0` 沿用 `step`；要做方形点阵按 `step_y ≈ step × 1080 / 2340` 传（同一个 `step` 会让 y 间距恒为 x 的 2.17 倍）。
4. **启动应用等就绪，可选同返首屏** —— `adb_app_start(package, serial="", wait_ready=True, with_screen=False, timeout_s=12, settle_ms=1200)`：
   - 就绪判据是「前台包名等于目标包名，且前台 Activity 自最后一次变化起稳定 `settle_ms`」，不是只看包名——有启动页的应用在启动页阶段包名就已经匹配。稳定窗口从首次采样算起，所以「应用本就在前台」不会拖到超时。
   - 返回 `ready` / `timed_out` / `activity` / `activity_changes` / `waited_ms` / `polls`；超时返回 `ready=false`，不抛错。
   - `with_screen=True` 时就绪后同返首屏（`ToolChunk`：JSON + PNG），复用截图实现，不落盘、长边 1024。
   - `wait_ready=False` 退回旧行为（拉起即返回，无就绪字段）。
5. **只读与并发标记** —— 只读工具标 `is_read_only=True`，有副作用的标 `is_concurrency_safe=False`。
6. **坐标一律归一化** —— 0~1，左上角 `(0,0)`，右下角 `(1,1)`，执行时按 `wm size` 换算。
7. **截图不落盘** —— 只以 base64 随结果返回，长边压到 1024 以内（截屏与网格图同口径），不写任何文件。
8. **文本输入支持 Unicode** —— `adb_input_text` 对 ASCII 走原 `input text`；含非 ASCII 时经设备输入法（ADBKeyboard）提交并恢复原输入法。工具层不下载、不写文件：设备未装时返回失败并给出 `python -m utils.adb_keyboard install --serial <serial>`；平台在 SOP 任务开始前经 `utils.adb_keyboard.ensure_ready()` 自动预装。APK 不入库（GPL-2.0）；少数 App 可能拒绝第三方输入法。

## 已知限制

### 视觉定位精度

坐标用归一化值，换算本身不损失精度（4 位小数在 1080 宽屏上不到 0.5 像素）。真正的误差来自模型看图的视觉估计，实测为 **0.03~0.08 归一化值**——该误差量级与屏幕分辨率无关，所以门槛以**归一化宽度**为准，px 只给参考机型的换算。

| 目标归一化宽度 | 参考 px（1440 宽 / 1080 宽） | 结果 |
| --- | --- | --- |
| ≥ 0.10 | ≥ 144 / ≥ 108 | 裸估可点中 |
| 0.04 ~ 0.10 | 58 ~ 144 / 43 ~ 108 | 裸估有风险，必须走点阵核对 |
| < 0.04 | < 58 / < 43 | 裸估不可靠；先用 `marker="ring"` 点阵核对，仍不解再换等价大目标 |

裸估的容错上限就是 0.03~0.08：目标宽度小于这个误差量级时，一次估点中不中要靠运气，不是靠手稳。

环点阵能把 0.04 以下的控件拉回「可核对」：环半径按点间距收敛，目标从环心透出，命中判定看行列号。前提仍是粗估点落在点阵窗口 `(size-1)×step` 内——它替代的是「看清哪个候选点压中」，不是「找到目标」。

实测：

- 1440×3040 天气页：居中的「更多」按钮纵向偏 90 px，右上角「+」偏 237 px，底部方框键只偏 17 px。
- 1080×2340 设置页：49×48 px 的右侧箭头徽标（归一化 0.045×0.021），`marker="ring"` + 5×5 + `step=0.02` / `step_y=0.01` 有 9 个环压中；取第 3 行第 3 列 `(0.904, 0.504)` 回填单点核对，红点正中箭头。

### 启动等待的真实收益（别按直觉估）

同一句任务「打开 com.govee.home → 我的 → 设置」，同一角色、同一提示词、每次先 `force-stop` 冷启动，四组实测：

| 变体 | 墙钟 | 轮次 | 工具调用 | 首点前截图 | 输入 token |
| --- | --- | --- | --- | --- | --- |
| `wait_ready=False`（旧行为） | **24.86 s** | 12 | 11 | 3 | 98,814 |
| `settle_ms=300` + 首屏 | 26.32 s | 10 | 9 | 1 | 85,706 |
| `settle_ms=600` | 26.37 s | 10 | 9 | 1 | 83,594 |
| `settle_ms=1200`（**默认**）+ 首屏 | 26.72 s | **9** | **8** | **0** | **78,184** |

结论要记住两条：

1. **省的是轮次与 token，不是时间**：模型的连拍截图本来就和 APP 冷启动并行，工具一旦同步阻塞等待，就吃掉了这段并行。墙钟反而 +1.5~1.9 s。
2. **`with_screen` 拿到的不一定是「加载完」的画面**：`activity` 稳定只说明主 Activity 已挂载，列表可能还在转圈（实测模型看到转圈会再补一张截图）。默认窗口已因此从 600 提到 1200 ms，首点前截图从 1 张降到 0。

按目标选：要省墙钟 → 传 `wait_ready=False`（回到 24.86 s）；要省 token → 用默认值（本次已确认按 token 优先定默认）。
