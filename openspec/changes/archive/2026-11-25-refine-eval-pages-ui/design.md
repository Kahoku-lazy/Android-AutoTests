## Context

三处界面（`/ai-assistant` 的发布、`/ai-assistant/evals`、`/ai-assistant/eval-cases`）都是同一批未提交 WIP 的产物：后端已把评测从「确定性尺子闸门」换成 LLM 裁判 + 真题集（`score_eval_target` / `eval-cases` / `eval-runs`），前端页面则是在这轮改造里新写的、没接共享件的一版。动机与范围见 `proposal.md - Why` 与 `What Changes`。

约束：

- 页面根已是 `doc-page doc-page--fixed wb-shell`，主题作用域正确；缺的是**页面内部**的组件装配。
- `.doc-body` 是 `display:flex; flex-direction:column`（`frontend/src/style.css:290`），`DoodleBtn` 是 `inline-flex`（`DoodleBtn.vue:42`）——所以任何直接挂在 `.doc-body` 下的按钮都会被拉成通栏。这是三页「通栏按钮」的唯一成因，不是有人写了 `width:100%`。
- 已有共享件充足：`WorkbenchCrumbs`、`FilterTabs`、`AppTable`、`ConfirmButton`、`SkeletonCard`/`EmptyState`/`ErrorState`、`.doc-section`、`--c-ai` / `--c-case` / `--app-marker-red` 等令牌。本变更**不新增共享件**。
- 测试基线：`frontend/tests/ai-assistant/p0/assistant-card.spec.ts:68-70` 断言助手卡动作恰为 `["配置","对话"]`；`eval-view.spec.ts:17-20` 断言 `scoreTone` 三档为 `--c-case` / `--c-dashboard` / `--c-element`。两条都会被本变更打破，必须同批更新。

## Goals / Non-Goals

**Goals:**

- 三页的层级、动作位置与数据语义回到「共享件唯一实现」：回退走面包屑条、动作进工具条、列表进表纸、危险动作走二次确认、三态齐备。
- 消除三页的可读性主因：口径文字墙（无条件渲染 + 整段等宽）、无 label 的裸输入、通栏动作条、卡外发布按钮、发布失败替换整块列表。
- 保持既有数据契约与业务口径不变：端点、信封、路由深度、`scoreTone` 之外的评分语义全部不动。

**Non-Goals:**

- 不启用 `EvalCase.note` / `EvalCase.enabled` 的写入（字段在 API 里已存在，但「作者能改备注与启停」属于产品决定，另单处理）。因此题库表纸不带「启用」列，编辑纸不带备注/启用字段——方案原型里出现的这两处，落地时按本单收窄。
- 不把评测看板的常驻 `iframe` 改成抽屉（P2）。
- 不做真题集步骤的增删（复用既有 `steps` 数组的编辑属于产品决定，另单）。
- 不改 `engines/eval` 的判分方法与 `/api/ai/eval-*` 契约。
- 不同步主 spec 与这批 WIP 之间的发布门禁口径（`assistant-eval` / `assistant-live-eval` 仍描述旧口径，属于 `score-assistant-with-deepeval` 的收尾）。

## Decisions

### 1. 通栏按钮：动装配，不动容器与按钮

把页面级动作放进工具条（flex 行）或面包屑行右端的按钮组，回退换成 `WorkbenchCrumbs`。**不改** `.doc-body` 的 `align-items`，也**不给** `DoodleBtn` 加 `align-self`。

- 备选 A：`.doc-body { align-items: flex-start }` —— 否决。它会让全站所有 `.doc-body` 里的块级子元素（分区纸、表格容器）一起收缩，等于给二十多个页面同时改版式。
- 备选 B：`DoodleBtn` 默认 `align-self: flex-start` —— 否决。表单里确实存在需要通栏的提交按钮，全局改成收缩会制造新的不一致；问题在「按钮被当成了页面动作」，不在按钮本身。

### 2. 分区用 `.doc-section`，不再自造 `.eval-page__panel`

`frontend-l3-content-block` 已规定「顶层分区块用 `.doc-section`」，`report-generator` 与 `bug-manager` 都在用。评测页改用三张 `.doc-section`（评分 / 真题集 / 历史），删掉页面私有的 `__panel` 容器样式。

- 备选：沿用模块内 `SectionBar` —— 它服务于「卡片网格分区」（助手看板），不带容器纸与内边距；在表单页里会让分区与卡片混成一层，故只用于页面内的次级标题，不用于分区容器。

### 3. 评测页把「口径」做成默认收起的可展开区，且未选对象时整体不渲染

现状把 `methods` 的 `v-for` 放在 `<template v-else>` 里、与 `targetId` 无关，所以未选对象也铺满 3 段 × 4 条 + `<pre>`。改为：未选对象时整块结果区不渲染；选中后口径为收起状态，展开后按指标分块、要点用列表（不用 `<pre>` 整段输出）。

- 备选：把口径挪到独立说明页 —— 否决。口径是「看分数时顺手核对判据」的上下文，离开结果就没意义。

### 4. 题库用「表纸 + 编辑纸（`el-dialog`）」，编辑不嵌进表行

表行里塞三列输入框会把可读性再毁一次（现状正是如此）。改为 `AppTable` 概览 + `el-dialog` 编辑，沿用 `frontend-l5-overlay` 的统一抽屉/弹层皮肤。

- 备选：行内展开（accordion）—— 否决。三列字段在 1440px 下已勉强，窄屏会退化；且行内展开与表纸的横向滚动叠加，滚动容器会打架。
- 保存写回：用 `PATCH` 返回的 `case` 替换数组内该项，不调 `load()`；仅新建与删除后按需重取，保证「输入与焦点不丢」。

### 5. 发布动作进卡片，草稿状态用独立胶囊

`AssistantCard` 已有动作行（`.assistant-card__actions`，1.5px 虚线，在白名单内）。草稿卡在该行下方加一条虚线分隔与第三个动作「发布」（语义色 `--c-case`，与今天 `DoodleBtn tone="teal"` 同色）；草稿标识从 `h3` 内联文本移到右上角独立胶囊。页面只传 `can-publish`，不再在卡片外包一层按钮。

- 备选：把发布做成卡片浮层按钮（hover 出现）—— 否决。发布是低频但不可发现即失败的动效，隐藏入口会让作者找不到。
- 卡片宽度不变：助手卡 `minmax(200px, 1fr)`、工作流卡固定 `280px`；三个动作放不下，所以发布单独成排。

### 6. 发布失败：页面级 `error` 拆成「卡级提示 + 轻提示」

现状 `error` 是页面级变量，`ErrorState v-if="error"` 会替换整个网格。改为：发布失败写入 `publishError[assistantId]`（卡内一行红字）并同时 `ElMessage.error`；`error` 只保留给列表加载失败。发布成功只替换该卡（或按需重取），不整页 `load()`。

- 备选：只用 `ElMessage` —— 否决。轻提示 3~6 秒消失，卡多时作者回头找不到是哪一张失败。

### 7. `scoreTone` 低分档改危险色

`helpers/eval-view.ts` 现返回 `--c-element`（薰衣草紫）表示低分，与「未达标」语义相反。改为 ≥0.8 `--c-case`、≥0.5 `--c-dashboard`、其余 `--app-marker-red`，并同步 `eval-view.spec.ts`。

- 备选：保留紫色、只用文字标注「未达 0.5」 —— 否决。分数卡是扫读场景，颜色是第一信号，文字是第二信号，不能互换。

## 模块防火墙自检

- 跨 App import：无。本变更只改 `frontend/src/modules/ai-assistant/**` 与一个 helper。
- 跨 App 写库：无。前端不直连数据库，也不新增写端点；题库保存继续走既有 `PATCH /api/ai/eval-cases/{id}/`。
- 新增 service/runner/consumer 依赖：无。
- 前端对后端的依赖：只经 `modules/ai-assistant/api/assistants.ts` 单一出口，未新增请求路径。
- 共享件方向：`modules/*` → `shared/components/*`，与现状一致；本变更不改共享件，只消费。

## Risks / Trade-offs

- [`assistant-card.spec.ts` 的动作列表断言会红] → 同批把断言改为「草稿三动作、已发布两动作」，并新增「卡内无卡外按钮」的断言。
- [`eval-view.spec.ts` 的档位断言会红] → 同批改为危险色，并加一条「低分不等于发布结论」的文案断言。
- [未选对象不渲染结果，可能让作者以为页面坏了] → 引导文案必须同时给出下一步（「先选一个评测对象」+ 对象选择就在同一屏），且主按钮在该状态下置灰而非消失。
- [口径收起降低可发现性] → 收起标题里带指标数量（「评测口径 · 3 项打分规则」），展开前就能知道里面有什么。
- [表纸 + 弹层比行内编辑多一次点击] → 换来的是字段可读与窄屏可用；题库规模是个位数到十几条，点击代价可接受。
- [发布动作挪进卡片后，卡片高度变化破坏网格对齐] → 网格 `align-items: start`，草稿卡比已发布卡高是预期结果；倾斜与硬影保持不变。
- [与 `score-assistant-with-deepeval` 的 8.5 任务语义重叠] → 该任务描述的是「加真题集页签」，工作树里其实已有实现（端点已改为 `eval-cases` / `eval-runs`）；本单只重排其版式，不改变能力归属，落地时在该单注明。

## Open Questions

- 题库是否要把 `note` / `enabled` 露给作者（当前只读不写）——影响的是编辑纸字段，不影响本单的 specs 与任务拆解，可后定。
- 真题集步骤是否允许增删 —— 同上，复用既有 `steps` 数组即可实现，但属于产品决定。
