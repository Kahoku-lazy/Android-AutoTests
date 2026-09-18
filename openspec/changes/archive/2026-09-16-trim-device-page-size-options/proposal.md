## Why

设备管理页（`/devices`）的「显示行数」组当前提供两个选项（`5` / `10`，`device-pool/constants.ts:45`）。
用户要求去掉「10」，只保留「5」。

现状（读码核实）：

- `PAGE_SIZE_OPTIONS` 是 **device-pool 模块私有**常量（`constants.ts:45`），与 `report-generator/constants.ts:23` 的同名常量（`[10, 20, 50, 100]`）互不相干；全仓只有 `device-pool` 的 `logic.ts` 与 `index.vue` 消费它。
- `DEFAULT_PAGE_SIZE` 已是 `5`（`constants.ts:46`），故默认行为不变。
- 共享 `usePagination` 只把 `options` 原样透传（`usePagination.ts:32`），对选项个数无约束；`setPageSize` 对单选项同样成立。
- 无测试引用该常量。

## What Changes

- `device-pool` 的 `PAGE_SIZE_OPTIONS` 由 `[5, 10]` 改为 `[5]`。
- 「显示行数」控件保留（用户口径是"只保留 5"，不是删除控件），渲染为单一选项且呈选中态；分页本身（`上一页 / 下一页`、`第 X / Y 页`）不受影响，数据超过 5 条时照常分页。
- 连带口径修正：`frontend-doodle-button` 的切换类 Scenario 原写「切换…「显示行数」…」，单选项后该交互不可达，需同步为「显示行数」只呈现选中态。
- `report-generator` 的分页选项、`frontend-l4-data-surface`「分页选项集来自模块 `constants.ts`」的口径**均不变**。

## 关联文档

- `dev_docs/文档编号对照表.md` **不存在**，故不引用 PRD/ARCH 编号。
- 依据报告：`dev_docs/DEV_TEST/设备管理页面设计元素清单-2026-09.md`（§2.9 行数按钮组）
- 相关 spec：`frontend-doodle-button`（切换类控件配色，本变更修正其 Scenario）、`frontend-l4-data-surface`（分页实现与选项来源，不改）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-doodle-button`: 「Device-management button groups assign tones by role」需要登记「显示行数」组为单一选项，并把它从"可切换"的 Scenario 里移出、补一条单选项 Scenario。

## Impact

- 前端页面：`/devices`
- 改动文件：`frontend/src/modules/device-pool/constants.ts`（一行）
- 无模板 / 样式 / 逻辑改动；无后端、无 API、无依赖、无路由变更
- 行为影响：设备表每页最多 5 行（原本默认也是 5），用户不再能切到 10 行
