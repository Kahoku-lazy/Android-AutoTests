## Why

清掉两处**会误导读者与未来用例的假信号**（都不改变用户可见行为，故 `.openspec.yaml` 置 `skip_specs: true`）：

1. **`data-testid="save-folder-cascader"` 永远不在 DOM 里**：真机探针显示「保存到元素定位」弹窗内只有 `save-page-select` / `save-confirm-btn` 两个 testid 能查到（`el-cascader` 不转发 `data-*`）。将来任何 `page.locator('[data-testid="save-folder-cascader"]')` 都会超时失败，而属性本身看起来像是「已备好测试钩子」。
2. **store 对外暴露两个组件从不消费的成员**：`analyzeSnapshot` / `clearChecked` 只被 store 内部调用，却出现在 `return` 的公开面上；与上一轮对 `devices` 暴露的处置口径不一致，也会让读者以为它们是给组件用的入口。

## What Changes

- `SaveToElementsDialog.vue`：「目录路径」的 `el-cascader` 外面包一层普通 `div` 并挂 `data-testid="save-folder-cascader"`（普通元素必定渲染该属性），包裹层补 `width: 100%` 保持布局；`el-cascader` 上原来的无效 `data-testid` 删除
- `store.ts`：从 `return` 中移除 `analyzeSnapshot` 与 `clearChecked`（两者仍是 store 内部函数，`capture` / `viewSnapshot` / `retry` / `applySnapshot` / `deleteSnapshot` 照旧调用）
- **BREAKING**：无（公开面的减法只影响本模块内部；组件从未消费这两个成员）

## 明确移出本变更范围

- 不改 `el-cascader` 的交互与校验（`:props` / `clearable` / `v-model` 均不动）
- 不为该 testid 补 e2e 用例（本变更只让钩子真实可用）
- 不改 store 的任何行为、状态与请求路径
- 不继续清理 `store.ts` 其它对外成员（`selected` / `filterMode` 等都有组件消费）

## 关联文档

- 需求编号：`PRD-03-设备检查器`（纯代码卫生，无需求变更）
- 依据的既有要求：`frontend-l2-page-region`「No L2 declaration without a consumer」（同一口径：不留无人消费的声明）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 无 spec 级行为变化，`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- `frontend/src/modules/device-inspector/components/SaveToElementsDialog.vue`（模板 1 处包裹 + CSS 1 行）
- `frontend/src/modules/device-inspector/store.ts`（`return` 去掉 2 个成员）
- 后端 / 端点 / 路由 / 依赖 / 迁移：零改动
- 观感变化：无（包裹层无样式副作用，宽度与原 `width: 100%` 一致）
- 恢复方式：`git revert`；无数据迁移