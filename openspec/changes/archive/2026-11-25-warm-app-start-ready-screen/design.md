## Context

`engines/ae_harness/tools/adb/tools.py` 的 `adb_app_start` 现在只有 5 行有效逻辑：`monkey -p <pkg> -c android.intent.category.LAUNCHER 1`，然后把 output 尾巴塞进 `_ok()`。它不读前台状态，所以「启动完了没有」只能由模型用截图猜。

真机实测（Govee Home / R5CT62RH88F，`temps/probe_app_start.py`、`temps/probe_app_ready.py`）：

| 时刻（相对 monkey 下发） | mResumedActivity | 说明 |
| --- | --- | --- |
| 383 ms | — | `monkey` 返回 |
| 3,084 ms | `com.govee.home/.HomeActivity` | 启动页 |
| 3,435 ms | `com.govee.home/.main.MainTabActivity` | 主界面 |
| 4,081 ms | 同上，已稳定 600 ms | 判就绪点 |

`dumpsys activity activities` 单次 125 ms（12 次轮询均值），200 ms 轮询间隔合理。`_front_package()` 已存在并解析 `mResumedActivity` / `mCurrentFocus`，无需新写系统调用。

同一任务的既有耗时结构：`app_start` 444 ms 返回 → 模型连拍 3 张截图（轮 3–5 各 629 / 1,038 / 1,243 ms）→ 才进入网格定位。这三轮合计 20.3K 输入 token。

## Goals / Non-Goals

**Goals**

1. 启动工具自己把「已就绪」等出来，并把这个事实告诉模型（Activity 名、等多久、是否超时）。
2. 就绪时把首屏图随同一次调用给出，省掉一次模型往返。
3. 默认开、可关；关掉后行为与现在逐字节一致。

**Non-Goals**

1. 不做视觉就绪判定（不靠截图比对判断「动画停了」）——代价是「同 Activity 内 splash」的应用判不准。
2. 不改 `adb_screenshot` / `adb_screenshot_grid` / `adb_dump_ui` 的返回契约。
3. 不改平台侧 `start_app` 工具与前端工具箱调试页。
4. 不新增工具（工具数仍 15）。

## Decisions

**D1 就绪信号用「Activity 变化后稳定」，不用「前台包名匹配」。** 实测包名在 +3 秒就满足了但还在启动页；只有看到 Activity 从 `HomeActivity` 变成 `main.MainTabActivity` 并稳定下来，才等价于「主界面已画出来」。备选「包名匹配即返回」被否：会把启动页当就绪，模型照着启动页去定位，错得更离谱。

**D2 稳定窗口 1200 ms，轮询 200 ms，上限 12 s。** 窗口必须大于 Activity 切换间隔（实测 3,084 → 3,435 = 351 ms），并且要盖住「主 Activity 已挂载、列表还在转圈」这一段——600 ms 时首屏图拍到的是转圈画面，模型仍会补一张截图（A/B 实测首点前还剩 1 张）；提到 1200 ms 后首点前截图降到 0。上限 12 s 覆盖冷启动 + 首装 dex 优化。超时返回 `ready=false` 而不是抛错：加载慢不等于失败，模型仍可自己截图等。

**D3 `with_screen` 复用截图实现，不新写压缩逻辑。** 直接调 `_screenshot_with_points(None, ...)` 拿 `ToolChunk`（JSON 元信息 + PNG），长边 1024 压缩、不落盘的口径与截图工具完全一致。备选「工具里自己 base64 塞进 JSON」被否：会绕开既有的图片压缩与 ToolChunk 语义，还会让模型看到两份不同的图片格式。

**D4 默认 `wait_ready=True`。** 这是执行模型最常用的入口，默认就该是「等好了再回来」；需要 fire-and-forget 的调用方（并发拉起、批量装机后统一检查）传 `False`。

**D5 提示词只加一句，不动截图工具。** 「`ready=true` 最多补一张确认截图，`ready=false` 才连拍」写在 `backend_bridge` 拼的用户消息里，和既有的「截图复用规则」并列。理由：工具已经给了事实，剩下的只是让模型别重复劳动；改截图工具会破坏既有精度契约。

## 收益重算（用实测数据，不用直觉）

同任务「打开 com.govee.home → 我的 → 设置」，同角色同提示词，每次先 `force-stop` 冷启动，四组实测：

| 变体 | 墙钟 | 轮次 | 工具调用 | 首点前截图 | 输入 token |
| --- | --- | --- | --- | --- | --- |
| `wait_ready=False`（旧行为） | **24.86 s** | 12 | 11 | 3 | 98,814 |
| `settle_ms=300` + 首屏 | 26.32 s | 10 | 9 | 1 | 85,706 |
| `settle_ms=600` + 首屏 | 26.37 s | 10 | 9 | 1 | 83,594 |
| `settle_ms=1200` + 首屏（**采用**） | 26.72 s | **9** | **8** | **0** | **78,184** |

结论要写清楚：**省的是轮次与 token，不是时间**——模型的连拍本来就与 APP 冷启动并行，工具一旦同步阻塞就吃掉了这段并行，墙钟反而 +1.9 s。前一版估算「省 2.4 s」是错的。

按目标取舍（已与需求方确认）：**token 优先**，故默认 `wait_ready=True` + `settle_ms=1200`；只要墙钟时可传 `wait_ready=False` 回到 24.86 s。

## Risks / Trade-offs

1. **同 Activity 内 splash 判不准**：稳定判据会立刻满足、`ready=true` 但画面还是启动页。缓解：`with_screen=True` 时模型看得到图会自己补截图，退化为现状，不会错点。
2. **每次启动多 0.1–0.5 s 轮询开销**：`wait_ready=False` 可关；对已经不冷启的应用首轮就稳定，只多一次 dumpsys（125 ms）。
3. **首屏图占上下文**：`with_screen` 出的图计入 `max_image_num=2`，可能把上一张更重要的图挤掉。缓解：只在启动这一步用，后续截图会自然补齐。
4. **慢设备上 12 s 上限可能不够**：超时已经降级为 `ready=false`，模型可继续等；后续可按真机数据调上限。
5. **返回形状分叉**：`with_screen=True` 返回 `ToolChunk`、默认返回纯文本，调用方与报告渲染都要能处理两种形状（截图工具已有先例）。

## Migration Plan

1. 工具加参数与等待循环（默认等待），先用 `temps/probe_app_ready.py` 的判据对齐实现。
2. 加 `with_screen`，复用 `_screenshot_with_points`。
3. 更新注入提示一句话。
4. 同任务 A/B：同一句「打开 Govee Home → 我的 → 设置 → 退出登录」，对比轮次、token、墙钟、是否仍一次点准。
5. 回退：把默认值改回 `wait_ready=False` 即可完全退回旧行为；`with_screen` 默认关闭不影响任何既有调用方。

## Open Questions

无。等待上限与稳定窗口已按实测落地（12 s / 1200 ms）；若某个应用的主 Activity 挂载后动画更长，再按真机数据调 `settle_ms`。
