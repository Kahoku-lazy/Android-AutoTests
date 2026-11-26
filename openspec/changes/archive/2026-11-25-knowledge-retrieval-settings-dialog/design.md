## Context

- 现状：`ModulePanel.vue` 在左栏顶部渲染 `<RetrievalSettingsCard v-if="canManage" />`，该卡片用 `AppCard` + `.sketch-kit` 表单平铺；`onMounted` 时同时拉 `fetchRetrievalSettings()` 与 `fetchEvalModelConfigs("embedding")`。
- 同模块已有两个 `el-dialog` 表单弹层：`ModuleFormDialog.vue`（`width="520px"`、`label-width="88px"`、`append-to-body`）与 `EvalTriggerDialog.vue`（同样式，`watch(visible)` 打开时拉模型列表）。两者是本变更的形态参照。
- 全局浮层契约（`openspec/specs/frontend-l5-overlay`）：含可编辑输入 MUST `:close-on-click-modal="false"`；内容持本地状态且每次打开需重置 SHALL `destroy-on-close`；可见性由本组件 `ref` 持有用 `v-model`；皮肤只在 `style.css`，模块不得补私有弹窗皮肤。
- 权限：检索配置读写仅超管（`GET/PUT /api/knowledge-search/settings/` 对普通用户 403），故入口与弹窗仍以 `canManage` 门控。

## Goals / Non-Goals

**Goals:**

1. 左栏首屏只留「知识模块」，检索配置收进「配置」按钮触发的弹窗。
2. 弹窗与同模块既有表单弹窗同形（宽 520、左标签 88px、底部取消/保存），不新造视觉。
3. 配置的读取时机跟弹窗生命周期走：打开即读、每次打开重读。

**Non-Goals:**

- 不改检索配置的字段、校验、索引作废口径与任何后端接口。
- 不改模块列表、勾选、提问、评测三条既有链路。
- 不为普通用户提供只读的检索配置视图（接口本就 403，维持超管专属）。
- 不新增「配置是否需要重建索引」的角标 / 提醒等新信息位。

## Decisions

**D1：`RetrievalSettingsCard.vue` 更名为 `RetrievalSettingsDialog.vue`，外层由 `AppCard` 换成 `el-dialog`。**
保留 `Card` 名而渲染弹窗会让后续检索误判层归属；更名成本仅两处 import。`el-dialog` 走全局纸面皮肤，符合「弹窗皮肤只在 `style.css`」的既有契约，也避免 `AppCard` 的微倾 + 图钉出现在浮层里。

**D2：加载时机从 `onMounted` 改为 `watch(visible)`，并在打开时清空上一次的 `settings` / `loadError`。**
弹窗若不重读，用户保存后关闭再打开会看到陈旧值（规格已明确每次打开 MUST 重读）。清空状态可避免「上一次加载失败的红字」残留到下一次打开。加载失败只落在弹窗内，不影响模块列表——这也是把配置移出页面流的附带收益。

**D3：表单沿用 `el-form label-width="88px" label-position="left"` + 原生 `el-input`，不再用 `.sketch-kit`。**
同模块两个既有弹窗都是这套写法，且 `.sketch-kit` 是卡片内容的手稿控件皮肤；在弹窗里混用会出现「虚线输入框 + 实线弹窗」双口径。字段与控件类型保持不变（`el-select` + `el-input` + `v-model.number`），零行为变化。

**D4：可见性由 `ModulePanel` 的 `settingsOpen` 持有，弹窗用 `defineModel<boolean>` 接收。**
符合 `frontend-l5-overlay` 的「本组件持有 `ref` → `v-model`」；与 `ModuleFormDialog` 的 `defineModel` 用法一致，不引入新范式。按钮只在 `canManage` 为真时渲染，弹窗组件也只在 `canManage` 时挂载。

**D5：`el-dialog` 带 `:close-on-click-modal="false"` + `destroy-on-close` + `append-to-body`。**
前者是含输入弹层的硬要求（误触遮罩会丢未保存值）；`destroy-on-close` 承接「每次打开重置」；`append-to-body` 避免 `.doc-body` 滚动容器与卡片 transform 影响遮罩覆盖。

**D6：入口按钮与标题进 `constants.ts`（`KS_RETRIEVAL_ENTRY` / `KS_RETRIEVAL_DIALOG_TITLE`）。**
仓库硬性规范禁止魔法字符串；同一文案被按钮与弹窗标题复用，集中存放避免两处漂移。

**D7：保存成功后只更新弹窗内 `settings`，不通知父级刷新模块列表。**
保存后的唯一外部影响是后端 `index_epoch` 变化（切块变了需重建索引）；模块列表行的内容不由此变化，因此不需要向上 emit，避免无谓的整页重载。

## 模块防火墙自检

- **跨 App import**：不涉及，只动 `frontend/src/modules/knowledge-search/`。
- **禁跨层依赖**：仅复用 `@/shared/components/DoodleBtn.vue` 与既有 `../api`、`../types`；无新增跨模块依赖。
- **写库收敛**：前端只经既有 `api.ts` 调 `PUT /api/knowledge-search/settings/`，不直连数据库。
- **仪表盘只读**：不涉及。
- **后端与引擎**：零改动。

## Risks / Trade-offs

- **[配置不再一眼可见，超管想确认当前向量模型要先点开弹窗]** → 需求明确要求不平铺；弹窗打开即读，成本是一次点击。若后续需要「当前配置摘要」，另开变更加只读摘要，不在本单夹带。
- **[每次打开都发两个请求（配置 + 模型列表）]** → 配置页本就低频操作，且模型列表在弹窗内才有意义；不引入缓存以免保存后读到旧值。
- **[弹窗与卡片共享的 `loadError` 文案可能在打开瞬间闪现]** → 打开时先清空 `loadError` 与 `settings`，加载态不渲染表单，失败只显示原因。
- **[删除卡片后左栏只剩一张卡，视觉上偏空]** → 左栏宽度由 `ks-split` 网格决定（280–360px），模块卡自然撑满，不需要补位元素。
