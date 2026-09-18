## Context

- 已具备：`engines/base.py` 的 `UiEngine` 协议与 `engines/android/airtest_u2.py` 的 `AirtestU2Engine` 已实现 `start_app/stop_app/click/swipe/input_text/press_key`；`apps/device_pool/session.py` 的 `DeviceSession` 已把这些原语包上 per-serial 锁并暴露 `start_app/stop_app/click/swipe/press_key`。
- 已具备：`apps/device_pool/pool.py` 的 `DevicePool`（`device` 单例）已公开 `action_click/action_longclick/action_swipe/action_drag/action_input`，但**缺 `start_app/stop_app/press_key` 三个包装**（它们只存在 `_session()` 私有入口）。
- 缺口：`apps/device_pool/api.py` `__all__` 有 `acquire_device/release_device/list_devices/device`，但**无"动作"白名单函数**，也没有统一"切设备 + 可用性/占用校验"的入口（该逻辑现散落在 `device_inspector/service.py` 的 `_check_device_available`/`ensure_current_device`，属内部实现，AI 不能 import）。
- 约束：AI 工具 handler 只允许 import 各模块 `api.py`（防火墙 #2）；设备交互（ADB/u2）归 device_pool 编排，禁止其他 App 直连引擎。

## Goals / Non-Goals

**Goals:**

- 经 `device_pool.api` 暴露 `use_device` + `device_action` 两个白名单函数，统一"切设备 → 校验 → 动作分发 → 返回前台"。
- 新增 AI 平台工具 `device_action`，handler 只调 `device_pool.api.device_action`。

**Non-Goals:**

- 不改 `DeviceSession`/`UiEngine` 协议与引擎实现（能力已存在）。
- 不重构 `device_inspector` 现有 `_check_device_available`/`ensure_current_device`（仅复刻守卫口径，不动其代码）。
- 不新增 WS/SSE；不做"点击后自动跳转判定"的组合工具（判定留给 AI ReAct 循环）。
- 不做 XPath 定位点击（引擎 `xpath_locate` 是可选能力，本次用坐标点击）。

## Decisions

**D1：动作统一经 `device_pool.api` 白名单暴露，AI 不直连 `device` 单例。**
`device_action` 收敛"校验 + 切换 + 分发 + 读前台"，AI 只 import `device_pool.api`。备选：让 AI `from apps.device_pool.api import device` 后直调 `device.action_*` —— 被否（绕过白名单、无法统一可用性/占用校验、违反"Tool 只调各模块 api.py"）。

**D2：点击/长按用设备像素坐标，坐标由 AI 从 `analyze_page` 的元素 `x/y/width/height` 取中心点。**
`click(x, y)` 直接命中 `DeviceSession.click` → 引擎。备选：按 XPath 定位点击 —— 被否（`EngineCapabilities.xpath_locate=False` 是当前路线 A，引擎不支持原语级 XPath 点击）。

**D3：`device_action` 每个动作执行后统一返回 `device.app_current()`（`package`/`activity`）。**
AI 用"动作前后前台是否变化"判定跳页（activity 变化 + 同 activity 下元素指纹变化双口径，指纹判定在 AI 侧用 `capture` 结果做）。备选：返回空/布尔 —— 被否（AI 需要原始前台信息，不能替 AI 下跳转结论）。

**D4：占用守卫 `_EXECUTION_OCCUPY_PREFIXES` 在 `device_pool.api` 复刻一份，不 import `device_inspector.service`。**
同一口径（`runner-/ai_agent/task-/run-`），两处独立维护，避免跨 App import 内部实现。备选：`device_pool.api` import `device_inspector.service` —— 被否（防火墙 #1 禁跨 App import service）。

**D5：导航走 `DeviceSession` TRANSIENT 惰性会话 + per-serial 锁，不 `acquire_device` 持业务锁。**
设备动作是短生命周期副作用，`session.py` 的 per-serial 锁已保证同设备操作串行；`acquire/release` 留给长时间独占爬取的后续封装。备选：先 `acquire_device` 再动作 —— 可行但增加锁泄漏路径，本次动作+抓取短链路不需要业务锁。

## 模块防火墙自检

- `device_pool/api.py` 新增函数只 import 本 App 的 `models/pool/service`，无跨 App import ✅。
- `ai_assistant/tool_registry.py` 新增 handler 只 import `apps.device_pool.api`（白名单），不 import `device_inspector.service`/`device_pool.service` 等内部实现 ✅。
- 设备动作是设备副作用，不写 `dp_` 表（不 acquire 不产生 DeviceLock/状态迁移）；无 INSERT/UPDATE/DELETE ✅。
- 无新增 WS/SSE 通道（复用现有 AI SSE 唯一通道）✅。

## Risks / Trade-offs

- [占用前缀双份维护（`device_inspector/service.py` 与 `device_pool/api.py`）可能漂移] → 两处加注释互指同口径；若后续再出现第三处消费，下沉 `shared/` 常量（本次不做）。
- [`devices/action` 新增未同步工具网关中间件白名单] → 任务阶段显式检查 `tool_gateway`/中间件白名单并同步（`ai_assistant/AGENTS.md` 明确要求）。
- [动作后前台未及时刷新（动画/异步加载中）] → `app_current()` 读引擎当前前台；AI 需要等待时用既有 `sleep` 工具再重读 `current`，工具本身保持原子不加 sleep。
- [坐标点击对动态列表/重复元素不稳定] → 唯一性筛选在 AI 侧（`count==1` 的 XPath 候选），设备动作层不内置该策略，避免过度设计。
