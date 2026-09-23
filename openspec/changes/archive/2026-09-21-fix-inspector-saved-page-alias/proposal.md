## Why

保存到元素定位时填的中文元素名（别名）在回看时**不显示**，而且回看态的元素名称格还**可以点进去改名——改完却无处落库**。

事实链（读码 + DB 核实）：

1. 保存时确实写了别名：检查器把内联重命名结果按 `resource_id` 映射成 `aliases`（`store.ts:259-266`），后端 `save_snapshot_to_elements` 写进元素（`apps/device_inspector/api.py:226-230`），`import_snapshot_page` 落库（`apps/element_locator/api_snapshot.py:148-149,171`）。
2. 读接口确实返回别名：`get_page_full` → `_element_dict` 带 `"alias": el.alias`（`api_snapshot.py:235`）。实测该库 5 个已保存页面里别名字段非空。
3. **前端把它丢了**：`store.ts:298-305` 的 `viewSavedPage` 逐字段映射元素时没有 `alias`；`StructureAnalysisPanel.vue:136-139` 的 `nameValue()` 是 `nameOverrides[_idx] ?? row.text`，于是名称列回落到元素的原始 `text`。
4. 同模块的既有口径恰恰是「别名优先」：`apps/element_locator/models.py:167` 就是 `alias or text_val or resource_id`，element-locator 自己的表也有「别名」列（`PageElementsWorkbench.vue:133,210-212`）。
5. 改名死路：`saveToElements` 需要 `snapshot_id`，而回看态 `snapshot_id` 为 `null`（`store.ts:307`）→ 保存按钮灰（`index.vue:19,79-87`）；用户在名称格敲进去的名字只留在 `nameOverrides` 里，随后被下一次 `applySnapshot` 清空。

这直接违反 `device-inspector-page`「元素表格勾选驱动筛减保存」的「元素名称…口径与快照视图一致」，也与「已保存页面…以只读方式在检查器中打开」相矛盾。

## What Changes

- `store.ts` 的 `viewSavedPage` 映射补上 `alias: e.alias`（后端已返回，纯补字段）
- `StructureAnalysisPanel.vue` 的 `nameValue()` 改为 `nameOverrides[_idx] ?? row.alias ?? (row.text || '')`，对齐 `models.py:167` 的优先级；快照模式下 `row.alias` 为 `undefined`，行为不变
- 回看态（无 `snapshot_id`）**禁用元素名称内联编辑**，让界面兑现「只读打开」：点击不再进入输入框，光标与图标不暗示可编辑
- **BREAKING**：无（名称列在回看态由「显示 text」变为「显示别名」，属缺陷修复）

## 明确移出本变更范围

- 「标识」列口径（`elLabel`）不动——别名只影响名称列，避免两列混同
- 校验 `alias` 是否需要可编辑回写（回看态本就只读，不做写回）
- 悬空媒体 404（④）、快照抽屉总数与错误净化（单 1）、截图坐标基准（单 2）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 既有口径依据：`apps/element_locator/models.py:167`（别名优先）、`device-inspector-page`「已保存页面选择器按行展示」（只读打开）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `device-inspector-page`: 修改「元素表格勾选驱动筛减保存」，补「回看时名称列优先显示已存别名」与「回看态名称不可改」两条口径

## Impact

- `frontend/src/modules/device-inspector/store.ts`（1 行：映射补 `alias`）
- `frontend/src/modules/device-inspector/components/StructureAnalysisPanel.vue`（名称取值优先级 + 只读守卫，约 6 行）
- 后端 / 端点 / 模型 / 迁移：零改动
- 规格：`device-inspector-page` 1 份 delta（1 改）