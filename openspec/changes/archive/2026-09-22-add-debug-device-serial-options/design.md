## Context

- 调试链路现状：`tools.py::get_tool_debug_schema()`（L536-559）用 `inspect.signature` 反射出每个参数的 `{name, type, required, default}`，`_annotation_type_name()` 只把注解归一到 `str/int/float/bool`；`invoke_platform_tool()`（L562-587）负责未知参数拒绝、必填校验与类型转换，是调用侧唯一裁判。
- 前端现状：`ToolDebugPage.vue`（L86-98）只有 `input[number|text]` 与 `checkbox` 两个分支；`useToolDebug.ts` 的 `defaultFormValues()` / `buildParams()` 按 `p.type` 处理，`watch(toolName, …, { immediate: true })` 使进页即拉 schema。
- 设备候选的既有只读来源：`apps/device_pool/api.py::list_devices(user_id)` —— 内部走 `is_device_visible`（管理员全局可见 / USB 恒公开 / WIFI 未锁定公开 / WIFI 锁定仅锁定者与配置者），返回 `serial`、`name`、`model`、`status`、`occupied_by`、`is_current` 等字段。同模块的 `get_online_devices()` 只按 `status=ONLINE` 过滤、**不做可见性收窄**，不可用于面向用户的候选。
- 设备状态只有 `ONLINE` / `BUSY` 两种（`models/constants.py`），离线设备由 `update_device_status()` 直接清除；因此「已连接在线」等价于 `status == ONLINE`。执行引擎占用（`RUNNER_OCCUPIED_PREFIXES`）的设备同时处于 BUSY。
- 需求见 proposal.md 与 specs/ai-platform-tool-debug；动机见 proposal.md - Why。

## Goals / Non-Goals

**Goals:**

- 设备管理分类下 5 个真正操作手机的工具，`serial` 从「可见 + 在线 + 未被占用」的设备中选择，并保留手输兜底。
- 设备可见性与候选口径只有一份实现，复用设备管理既有逻辑，不新开第二处判定。

**Non-Goals:**

- 不改 `acquire_device` / `release_device`：它们是设备池占用记账，不操作手机。
- 不做其他分类（`screenshot_page`、`ocr_page`、工作流的目录与文档）的参数候选。
- 不做静态枚举（动作类型、方向、释放原因）与 `package` 级联候选（后者需连设备、有副作用，是独立问题）。
- 不新增接口，不改工具运行时装配与「交给助手」启停语义，不做数据库迁移。

## Decisions

**D1 候选内联进调试 schema 响应，不新增端点。** 理由：本单场景无级联、无副作用，候选规模为个位到几十；内联可省掉第二个请求与随之而来的加载态、失败态与级联状态机。备选：单独的 `options` 只读端点 → 本单否决，它是为「级联参数」与「读取有副作用」设计的，收窄范围后不存在该需求。

**D2 `get_tool_debug_schema()` 保持纯函数，候选由视图层解析。** schema 函数只输出该参数的候选声明；视图层拿到 `request.user_id` 后查设备并填入候选清单。理由：可见性收窄需要请求者身份，纯函数不应依赖请求上下文，保持可单测。备选：把 `user_id` 传进 schema 函数 → 否决，会让一个纯反射函数开始依赖 ORM 与请求语义。

**D3 候选取数复用 `apps/device_pool/api.py::list_devices(user_id)`，在其结果上过滤 `status == ONLINE` 且 `occupied_by` 为空。** MUST NOT 改用 `get_online_devices()`：它缺可见性收窄，会把 WIFI 锁定设备暴露给无权用户。理由：可见性是安全边界，第二处判定必然与设备管理页漂移。

**D4 候选登记与工具同源。** 在 `tools.py` 用一张「工具名 → 参数名」的小表登记这 5 个工具的 `serial`，未登记的参数不带候选。理由：前端 MUST NOT 按参数名硬编码（项目禁止魔法字符串），同时避免在 schema 函数里散落工具名分支。

**D5 前端候选参数用 Element Plus 可过滤下拉并保留手输。** `el-select` + `filterable` + `allow-create`，由 Element Plus 承担定位与键盘可达（沿用项目既有约定）。候选为空、加载失败各有可读提示，MUST NOT 阻止执行。`buildParams()` 现有「空值且非必填则省略该参数」的行为必须保持，下拉的「清空」映射为省略而非提交空串。

**D6 纯增量，向后兼容。** 候选是参数上的可选信息，无可选值的参数 schema 与现状逐字段一致，不识别候选的渲染方仍按输入框工作。前后端同仓同版本发布，无灰度需求。

## 模块防火墙自检

- **跨 App import**：只读调用 `apps/device_pool/api.py::list_devices`；MUST NOT import 其 `models` / `service` / `state_machine` / `views`。`tools.py` 既有的 device_pool Model 只读用法不变，本变更不新增。
- **写操作收敛**：本变更无写操作、无新增端点，候选取数为纯读；不产生任何 INSERT/UPDATE/DELETE。
- **前端 HTTP 出口**：只经 `frontend/src/modules/ai-assistant/api/toolbox.ts` → `shared/api-client`；不新增 axios 直连或裸 fetch。
- **内部网关**：MUST NOT 走 `/api/ai/tools/{module}/{action}` 内部令牌网关（沿用既有约束）。
- **数据库**：前端不直连；本变更无迁移。

## Risks / Trade-offs

- [候选与提交瞬间漂移：选完设备后被他人占用] → 工具自身 `use_device` 校验仍是唯一裁判，错误按既有路径展示。
- [可见性泄露] → 复用 `list_devices(user_id)`；单测断言非超管候选等于其可见、在线、未被占用的设备集合。
- [`status` 与 `occupied_by` 历史数据不一致，出现「ONLINE 但仍有占用者」] → 两个条件同时成立才入候选。
- [候选为空让用户以为该参数不可用] → 行内可读提示 + 保持手输可提交。
- [只覆盖这 5 个工具，其他分类的 `serial` 仍是输入框] → 有意为之（本轮范围），后续按同一机制增量扩。

## Migration Plan

- 交付顺序：后端先加候选登记与解析（旧前端不受影响，只是多一个不认识的字段），再切前端渲染。
- 回滚：前端退回统一输入框渲染即可；后端新增字段为纯增量，可保留。无数据库迁移需回滚。

## Open Questions

- 是否把设备检查器 / 视觉识别分类的 `screenshot_page`、`ocr_page` 也纳入同一候选机制？本单不做。
- `acquire_device` / `release_device` 之后是否需要各自语义的候选（在线空闲 / 使用中）？本单不做。
