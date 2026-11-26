## Why

评测页、评测题库页与助手看板上的「发布」是同一个病：都没接共享件，于是每页各自长出一套原生控件。三页里现在同时存在通栏按钮（`.doc-body` 是 flex column、`DoodleBtn` 是 inline-flex，被 stretch 拉满）、无 label 的裸输入框、原生 `select` / `table` / `checkbox`，以及挂在卡片外面、压着硬阴影的「发布」；评测页还把「评测口径」的 3 段 × 4 条长句**无条件**铺在正文里，形成一屏文字墙。可读性与主题一致性因此同时失守，且发布失败会把整块助手看板替换成错误态。

## What Changes

- **评测页**：回退改面包屑条、页面动作收进工具条（不再有通栏按钮）；对象未选时只留一句引导，不渲染评分结果、真题集与口径正文；评测口径默认收起；结果按「评分 / 真题集 / 历史」三张分区纸组织；历史表「分数」列改回分数（现在该列渲染的是提示词指纹）；手写分段控件、原生下拉与原生表换 `FilterTabs` / Element Plus 表单皮肤 / `AppTable`。
- **评测题库页**：四个裸 `input` 换成「表格纸 + 编辑纸」；字段带 label；删除走二次确认；保存只更新该行（不再整页重载，编辑内容与焦点不丢）；补空态与加载态。
- **助手看板发布**：发布从卡片外收进卡片动作行（草稿卡的第三个动作）；草稿标识从名称内联词改为右上角独立胶囊；发布失败只提示该卡、不替换整块列表。
- `scoreTone` 低分档改用危险色令牌（现有 `--c-element` 与「未达标」语义不符）。
- 非目标：不改评测与发布的业务口径（评分不阻断发布）、不动 `/api/ai/eval-*` 契约、不加侧栏入口、不实现新评测能力、不做真机基线。

## 关联文档

无关联 PRD 编号：本变更只重排既有三处界面的版式与共享件装配，不新增产品功能页。设计依据是方案与可点原型 `temps/ai-eval-ui-redesign-proto.html`。

## Capabilities

### New Capabilities

- `frontend-eval-pages`: 评测页与评测题库页的展示与交互契约——未选对象时的空白态、口径折叠、评分/真题/历史三区的数据语义、题库的表格纸与编辑纸、删除二次确认、保存局部更新。

### Modified Capabilities

- `frontend-doodle-subpage-nav`: 新增「评测页与题库页以面包屑条承载回退」的要求；页面级动作不得作为 `.doc-body` 顶层裸按钮。
- `ai-assistant-card`: 卡片动作由「配置 / 对话」两项扩为草稿卡可带第三个卡内动作「发布」；草稿标识改为独立胶囊；发布失败不得让列表其它部分消失。

## Impact

- 代码：`frontend/src/modules/ai-assistant/{evals.vue, eval-cases.vue, index.vue, components/SopWorkflowSection.vue, components/AssistantCard.vue, helpers/eval-view.ts}`；复用 `WorkbenchCrumbs` / `FilterTabs` / `AppTable` / `ConfirmButton` / `SkeletonCard` / `EmptyState` / `ErrorState` 与 `--c-ai` 等既有令牌，不改共享件本身。
- 测试：`frontend/tests/ai-assistant/p0/assistant-card.spec.ts`（动作列表断言）与 `eval-view.spec.ts`（`scoreTone` 档位）需同步；新增评测页与题库页的 p0 用例。
- API：无。端点、方法与信封不变；题库保存仍走既有 `PATCH /api/ai/eval-cases/{id}/`。
- 文档：`.agents/docs/frontend/ai_assistant/*` 若描述页面构成，按新分区与动作行更新。
- 不在范围：`score-assistant-with-deepeval` 任务 8.6 的真机基线分；主 spec 与该批 WIP 之间的发布门禁口径同步。
