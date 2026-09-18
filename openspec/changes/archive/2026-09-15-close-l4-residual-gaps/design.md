## Context

`report-generator` 三处常量实测：`constants.ts:23,27,28` 定义 `PAGE_SIZE_OPTIONS=[10,50,100]` / `TABLE_HEADER_HEIGHT=54` / `TABLE_ROW_HEIGHT=50`，**全仓无 import**；`ReportDetail.vue:29-31` 有本地 `[10,20,50,100]` / `45` / `41`（`tableScrollY` 用后两者）；`index.vue:120` 用内联 `[10,50,100]`。

`AgentBasicInfo.vue:22` 的 `名称` 有 `required`，但父组件 `AgentDetail.save():123-129` 在 `payload.name` 为空时取线路名或「平台小助手」，字段实际非必填。

## Goals / Non-Goals

**Goals:**

- 让 `report-generator/constants.ts` 成为分页/表高的唯一真相源，消除死常量与三处重复
- 移除最后一处「仅 `required`」的误导星号，使该项缺口真正归零

**Non-Goals:**

- 不改 `device-pool` 的分页常量（它有自己模块的 `constants.ts`，本就是独立真相源）
- 不改「空名取默认名」的既有行为（本次只去掉星号，不禁止空名）
- 不统一报告列表与详情页之外的其它分页选项（无其它消费方）
- 不动 `AppTable` 与 3 处原生 `el-table`（另开变更 `extend-apptable-capabilities`）

## Decisions

**D1 · `TABLE_*` 取详情页现值（45 / 41），零行为变化**

`TABLE_HEADER_HEIGHT` / `TABLE_ROW_HEIGHT` 的唯一消费方就是 `ReportDetail`（`tableScrollY`），`constants.ts` 里的 54 / 50 是零消费的过期值。改为 45 / 41 不改变任何渲染结果。

**D2 · `PAGE_SIZE_OPTIONS` 统一为 `[10, 20, 50, 100]`（按裁决）**

列表页由此新增「20」档，属**可见变化**；详情页不变。两处都从 `constants.ts` 导入，模板取用同一常量。

**D3 · `index.vue` 用导入常量替代解构出的 `PAGE_SIZE_OPTIONS`**

`usePagination` 会返回同名 `PAGE_SIZE_OPTIONS`，若同时 import 会命名冲突。做法：从解构中移除该名，模板改用导入的常量，并把 `options` 传为同一常量——避免别名，也避免两份同名变量。

**D4 · `AgentBasicInfo` 移除 `required` 而非补 `:rules`**

该字段空值有显式默认兜底，语义上非必填；加 `:rules` 会把「空名取默认名」变成「空名禁止提交」，属行为变更。移除星号让 UI 与实际契约一致，且零行为变化。

## 模块防火墙自检

- 跨 App import：不涉及。只改 `frontend/src` 内部
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无

## Risks / Trade-offs

- [列表页新增「20」档后，若用户选「20」再切到详情页，选项集已一致故无不一致问题] → 两处现在同源，属修复而非风险
- [`index.vue` 从解构里拿掉 `PAGE_SIZE_OPTIONS` 后若模板仍有残留引用会编译失败] → 模板用的就是导入常量，`vue-tsc` 会校验；改动后必跑 typecheck
- [删除 `constants.ts` 的 54 / 50 会丢失「原设计值」] → 它们零消费，属死代码；如需保留意图，注释说明以详情页实测值为准

## Migration Plan

- 无数据迁移；回滚为 revert 本变更提交
- 验证顺序：`vue-tsc --noEmit`（改动文件零错误）→ `vue-frontend-check` → 报告列表分页 / Agent 基本信息页浏览器目视（本环境待补）
