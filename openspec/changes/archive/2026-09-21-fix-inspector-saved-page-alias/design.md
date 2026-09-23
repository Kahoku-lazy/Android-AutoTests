## Context

- 别名链路（读码核实）：前端 `aliases` 按 `resource_id` 组装（`store.ts:259-266`）→ 后端落库（`device_inspector/api.py:226-230`、`element_locator/api_snapshot.py:148-149,171`）→ 读回（`api_snapshot.py:235`）→ **前端丢弃**（`store.ts:298-305` 未映射 `alias`）。
- 名称渲染：`StructureAnalysisPanel.vue:136-139` `nameValue(row)` = `store.nameOverrides[row._idx] ?? (row.text || '')`；`:295-303` 的名称格单击即 `startEdit`。
- 既有口径：`apps/element_locator/models.py:167` 为 `alias or text_val or resource_id or f"El #{id}"`；`PageElementsWorkbench.vue:133,210-212` 有独立「别名」列可编辑（那是元素定位的写入口）。
- 回看态只读的规格依据：`device-inspector-page`「已保存页面选择器按行展示」要求「点击页面 MUST 仍以只读方式在检查器中打开该页」。
- 改名死路证据：`store.ts:244,276` 的 `saveToElements` 以 `snapshot.value.snapshot_id` 为前置；回看态该值为 `null`（`store.ts:307`），`index.vue:19` 的 `canSaveToElements` 为假 → 保存弹窗打不开。
- 当前无自动化断言：`device-inspector` 尚无单测（单 1 会补 store 用例，本单依赖真机读数）。

## Goals / Non-Goals

**Goals:**

- 回看时名称列显示与服务端一致的别名（缺失才回落文本）
- 回看态界面与「只读打开」一致：名称不可改、无编辑暗示
- 快照模式行为零变化

**Non-Goals:**

- 不改「标识」列（`elLabel` 仍按 text → content_desc → resource_id → class）
- 不在回看态提供改名写回（那是元素定位的职责与入口）
- 不改后端返回结构与 `_element_dict`（已提供 `alias`）
- 不解决后端按 `resource_id` 回填别名导致的同 rid 覆盖问题（另开：属保存侧语义）

## Decisions

**D1 `viewSavedPage` 补 `alias`，`nameValue` 采用「用户当次改名 → 别名 → 文本」优先级**
理由：与 `models.py:167` 的服务端口径一致；`nameOverrides` 仍排第一，因为快照模式下的当次内联改名必须优先（该模式 `row.alias` 为 `undefined`，故对快照模式无影响）。
备选：把别名塞进 `text`（`text: e.alias || e.text_val`）→ 否决：`elLabel` 读 `e.text`，「标识」列会跟着显示别名，两列口径混同。
备选：在组件里额外维护一份 alias 映射 → 否决：数据已在 `row` 上，绕路只会多一处同步点。

**D2 回看态禁用名称内联编辑**
判据用 `store.snapshot?.snapshot_id` 是否存在（与 `canSaveToElements` 同源），名称格在只读态不绑 `startEdit`、不可聚焦、图标不出现。
备选：保留可编辑但只留在本地 → 否决：用户会以为改了名，实际下次打开就丢；与「只读」表述矛盾。
备选：让回看态改名也能写回 → 否决：需要新增一个写接口与冲突语义，超出本单，且规格明确只读。

## 模块防火墙自检

- 跨 App import：零新增（只补一个字段映射与一个只读守卫）
- 跨 App import service/runner/consumer/state_machine：不涉及
- 写库收敛 api.py：不涉及（无后端改动、无新增写路径）
- 前端不直连数据库：不涉及
- HTTP 出口：不变（不新增请求）
- 共享层：不改 `AppTable` / `EmptyState` / `tokens.css`
- 后端 / 端点 / 路由 / 迁移：零改动

## Risks / Trade-offs

- [只读守卫误伤快照模式] → 判据只看 `snapshot_id`；快照模式仍可改名（保存时作为 `aliases` 落库），真机两种模式各走一遍
- [别名与文本相同导致看不出差别] → 真机选一个有别名且文本不同的元素（库内已存在，如 `com.govee.home:id/ivTabDevice`）
- [与单 1 / 单 2 同文件冲突] → 本单动 `store.ts` 的 `viewSavedPage`（单 1 动错误分支与 `deleteSnapshot`）与 `StructureAnalysisPanel.vue`（其余单不动该文件）；改动点不同行，`git diff` 可分离

## Migration Plan

1. `store.ts` 补 `alias` → `nameValue` 优先级 → 只读守卫
2. 真机：打开「已保存页面」选中一条含别名的页面，核对名称列与元素定位的「别名」列一致；快照模式下核对仍可改名且保存后别名生效
3. 门禁：`npm run lint:styles`、`npx vite build`、真机走查
4. 归档：delta 写入 `device-inspector-page`
5. 回滚：`git revert`；无数据迁移

## Open Questions

（无）
