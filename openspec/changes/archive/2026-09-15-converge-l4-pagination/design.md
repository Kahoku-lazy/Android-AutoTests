## Context

`ReportDetail.vue`（457 行）的用例明细表用一套本页状态机分页：`pageSize = ref(20)`、`currentPage = ref(1)`、`totalPages`、`pagedCases`、`goPage`、`setPageSize`；`tableScrollY` 还依赖 `pageSize` 做行高联动。共享 `usePagination.ts`（64 行）返回同形 API，另有两处已合规消费方（`report-generator/index`、`device-pool/DevicePoolView.logic`）。

实测发现一处**既有常量漂移**（不在本变更范围）：`ReportDetail.vue:28-30` 的本地 `PAGE_SIZE_OPTIONS = [10, 20, 50, 100]` / `TABLE_HEADER_HEIGHT = 45` / `TABLE_ROW_HEIGHT = 41`，与 `report-generator/constants.ts:23,27,28` 的 `[10, 50, 100]` / `54` / `50` **取值不同**；模块 `AGENTS.md` 要求常量经 `constants.ts`。

## Goals / Non-Goals

**Goals:**

- 退役 `ReportDetail.vue` 的分页状态机，改用共享 `usePagination`，行为逐项不变
- 修正 `usePagination.ts` JSDoc 中不存在的 `AnimalButton`
- 在 spec 与 L4 速查中收回该例外

**Non-Goals:**

- 不改默认每页 20 行与选项集 10 / 20 / 50 / 100（改了就是行为变更）
- 不收敛 `ReportDetail` 本地 `PAGE_SIZE_OPTIONS` / `TABLE_*` 与 `constants.ts` 的取值漂移（属独立问题，本变更只登记）
- 不统一三处分页的渲染写法（`el-button` / 原生 `button` / `el-button size=small`）——spec 只约束实现唯一，未约束外观唯一
- 不改 `device-pool` 与 `report-generator/index` 的既有分页调用

## Decisions

**D1 · 用 `usePagination` 的 `options` 传本页现有选项集，保证零行为变化**

`usePagination(allCases, { pageSize: 20, options: PAGE_SIZE_OPTIONS })` 保留默认 20 与 10 / 20 / 50 / 100。备选「改用 `constants.ts` 的 `[10, 50, 100]`」会删掉「20」这一档并改变默认值，属行为变更，不采纳。

**D2 · 只换状态机，不动模板与文案**

`pagedCases` 以 `pagedItems: pagedCases` 重命名映射，模板 `<AppTable :data-source="pagedCases">` 与分页控件一行不改，把 diff 限制在脚本层，便于 review 与回滚。

**D3 · 常量漂移只登记、不顺手改**

`ReportDetail` 本地常量与 `constants.ts` 取值不同是既有问题，修它会改变表格高度与可选行数（可见行为变化），超出本变更范围；按「只碰必须碰的」登记进 L4 速查 §⑥ 已知缺口。

**D4 · 用 MODIFIED 收回需求，而不是删除需求条目**

「分页唯一实现」这条契约继续有效，只是例外退役；改写其第二个场景即可，避免 spec 出现无需求可依的空档。

## 模块防火墙自检

- 跨 App import：不涉及。只改 `frontend/src` 内部，无 Django App 间 import 变化
- 禁止跨 App import service / runner / consumer / state_machine：不涉及
- 所有 INSERT / UPDATE / DELETE 收敛到各 App 的 api.py：不涉及，无后端写操作
- 前端不直连数据库；仪表盘不做写操作：不涉及，不改任何 `api.ts` / HTTP 调用
- 新增跨模块依赖：无（`usePagination` 是既有 shared composable）

## Risks / Trade-offs

- [composable 的 `goPage` 带 `if (p !== current.value)` 早退，与旧实现「无条件赋值」在「同页重复点击」上略有差异] → 无可见影响（同页赋值即无操作）；目视时点一次上一页 / 下一页确认无跳页
- [`pagedItems` 是 computed，若 `allCases` 长度在筛选后收缩，`currentPage` 可能悬空] → 旧实现同样不夹取；`usePagination` 的 `totalPages` 用 `Math.max(1, …)`，与旧实现一致，行为不变
- [`tableScrollY` 依赖 composable 返回的 `pageSize`，若解构遗漏会静默失灵] → 解构时显式取 `pageSize`，并以 `vue-tsc` 与目视双重确认表高随行数变化
- [spec / 速查的例外退役后若代码回退会造成文档与实现不一致] → 交付前用 `rg` 确认全仓不再存在自算 `totalPages` 的分页状态机

## Migration Plan

- 无数据迁移，纯前端实现替换；回滚为 revert 本变更提交
- 验证顺序：`vue-tsc --noEmit`（改动文件零错误）→ `vue-frontend-check` 静态扫描 → 报告详情页分页目视（浏览器，本环境待补）
