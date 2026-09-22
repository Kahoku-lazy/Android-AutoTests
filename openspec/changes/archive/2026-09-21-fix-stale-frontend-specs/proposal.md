## Why

`npx vitest run` 当前有 **5 个文件 / 17 个用例红**，且这 5 个文件在 HEAD 是**已提交且干净**的（不是并发开发中的半成品）——它们是几次重构后被落下的断言（逐条证据见 design.md「Context」）：

1. **device-pool 端点封装（11 例）**：`api.spec.ts` 表里 11 条 `url` 全缺尾斜杠，而 `device-pool/api.ts` 的 8 个端点在提交 `51e4809e`（路由统一带尾斜杠）之后全部带尾斜杠。
2. **device-pool 分页（1 例）**：`DevicePoolView.logic.spec.ts:104` 期望 12 台设备 → 2 页；实际 `DEFAULT_PAGE_SIZE = 5`，应为 3 页。
3. **仪表盘：被测组件已删除（收集到 0 用例）**：`ModuleNavigator.spec.ts` 导入的组件在提交 `e51acebd` 中删除，HEAD 已不存在、`src/` 中 0 引用，该文件只会以 import 解析失败告终。
4. **仪表盘：stats DTO 已瘦身（4 例）**：`useDashboardStats.spec.ts` 的 fixture 与断言仍含 `trend` / `reports` / `workflow.page_flows` / `new_cases` 等字段，真实契约（`shared/types/dashboard.ts`、`apps/dashboard/views.py`）没有它们。
5. **仪表盘：元素域已下线（1 例）**：`DashboardView.logic.spec.ts:121-122` 期望 `elementBreakdown` 三类 `[android, web, api]`，而归档 change `2026-09-21-remove-element-locator-web-api` 之后只保留 android。

共性是**测试资产没有跟随已提交的产品决定**：本轮只让测试对齐现状，不反向要求产品恢复已删除的东西。

## What Changes

| 文件 | 改动 |
|------|------|
| `tests/device-pool/p0/api.spec.ts` | 11 条 `url` 补尾斜杠（`/devices/scan` 3 条、`/devices/S1` 2 条，以及 `/devices`、`/devices/S1/activate`、`/lock`、`/release`、`/disconnect`、`/devices/heartbeat` 各 1 条） |
| `tests/device-pool/p1/DevicePoolView.logic.spec.ts` | 第 104 行 `toBe(2)` → `toBe(3)` |
| `tests/dashboard/p1/ModuleNavigator.spec.ts` | **删除**（被测组件 HEAD 已不存在） |
| `tests/dashboard/p0/useDashboardStats.spec.ts` | fixture 与 4 个用例的断言对齐真实 DTO：删掉已消失字段，保留逐字段映射、空值回退、部分缺字段回退的覆盖 |
| `tests/dashboard/p1/DashboardView.logic.spec.ts` | 第 121-122 行 `elementBreakdown` 期望 3 类 → 1 类 `[android]` |
| `tests/README.md`、`tests/dashboard/p2/README.md` | 登记表随文件删除更新（dashboard P1 文件数 4→3、说明去掉「导航」；不再提 ModuleNavigator） |

**BREAKING**：无。只改测试资产与测试登记表，产品代码（`src/**`、`apps/**`）、端点、迁移零改动。

## 明确移出本变更范围

- 不恢复 `ModuleNavigator` 组件；不恢复 `trend` / `reports` / `page_flows` / `new_cases` 字段；不恢复 Web/API 元素域。这三者都是归档 change 里有意的移除，本单不改产品决定。
- 不碰 `src/**` 与 `apps/**` 任何一行。
- 不顺手修别的模块（本次全量 vitest 中只有这 5 个文件红）。
- 不改 `PRIORITY_TEMPLATE.md` 的优先级约定与用例命名规范。

## 关联文档

- 相关归档：`2026-09-21-remove-element-locator-web-api`（元素域三→一，本单第 5 组的上游决定）
- 上游提交：`51e4809e`（路由尾斜杠）、`e51acebd`（ModuleNavigator 删除）、`7406e603`（dashboard 模块重构 / DTO 瘦身）
- 后端契约来源：`apps/dashboard/views.py:124-151`

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——本变更不改变任何系统行为，只让测试断言与既有行为一致；`.openspec.yaml` 声明 `skip_specs: true`）

## Impact

- 测试资产：`frontend/tests/` 下 5 个 spec 文件（1 删 4 改）+ 2 个 README
- 产品代码 / 端点 / 迁移：零改动
- 可见行为变化：无（dashboard 少一个「已删除组件的测试文件」，UI 与接口一字未动）
- 门禁收益：`npx vitest run` 由 5 文件 17 例红 → 全绿；`npx vue-tsc --noEmit` 由这 4 个 spec 造成的类型报错清零
