## Context

动机见 `proposal.md - Why`。约束（读码核实）：

- `PAGE_SIZE_OPTIONS` 为 device-pool 私有常量，唯一消费链：`constants.ts:45` → `DevicePoolView.logic.ts:19,162` → `usePagination` → `index.vue:124` 的 `v-for`。
- `DevicePoolView.logic.ts:167` 的表高 `TABLE_HEADER_HEIGHT_PX + pageSize * TABLE_ROW_HEIGHT_PX` 跟随 `pageSize`，单选项下恒为 `54 + 5×64`。
- `usePagination`（`shared/composables/usePagination.ts:31-63`）对 `options` 无个数校验，`setPageSize` 直接赋值并复位到第 1 页。

## Goals / Non-Goals

**Goals:**

- 「显示行数」只剩 `5`；分页行为与表高随之收敛到单一取值。

**Non-Goals:**

- 不删除「显示行数」控件、不改模板与样式（用户口径是"只保留 5"）。
- 不改 `report-generator` 的 `PAGE_SIZE_OPTIONS`（`[10, 20, 50, 100]`）。
- 不改共享 `usePagination` 的默认 `options`。
- 不删设备页切换类皮肤里 `.page-size-btn:not(.active)` 那条天蓝规则——它表达的是该组的契约，选项增加时即生效；本变更只登记它当前不可达。

## Decisions

### D1 只改常量值，不动控件

`[5, 10]` → `[5]`。备选（顺带删掉整个「显示行数」控件）会改动模板、样式与 `setPageSize` 的可达性，属需求之外，否决。

### D2 同步修正 `frontend-doodle-button` 的 Scenario

该 spec 的切换类 Scenario 明确写「切换…「显示行数」…」。单选项后这一交互不可达，属 spec 与实际不符，需以 MODIFIED 修正（把「显示行数」移出可切换列表 + 补一条单选项 Scenario），而不是留着一条跑不通的场景。

## 模块防火墙自检

- 跨 App import / ORM 写 / 前端直连数据库 / 新增依赖 / API 契约 / 路由：**均不涉及**（改的是一个模块内数字数组）。纯前端常量改动。

## Risks / Trade-offs

- [用户仍想要 10 行/页] → 回滚成本是一行常量；已在 proposal 明写"不再能切到 10 行"。
- [残留一条当前不可达的天蓝规则] → 已在 spec 与该组的口径里登记为"契约保留"，非遗漏。
