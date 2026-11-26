## 1. 基线与护栏

- [x] 1.1 记录前端基线：在 `frontend/` 跑 `npm run test -- ai-assistant`，记下当前通过项，并确认 `assistant-card.spec.ts` 的动作列表断言（`["配置","对话"]`）与 `eval-view.spec.ts` 的档位断言（`--c-element`）是本单会打破的两处。验证：基线数字写进本任务交付说明。
- [x] 1.2 把评测页与题库页的纯数据构造下沉到 `helpers/eval-view.ts`：历史行（时间 / 指标与分数 / 指纹）、评分卡（分数 / 档位 / 是否未达标）、题目行（题目 / 步数）。组件只负责渲染。验证：`npm run typecheck` 通过，页面内不再出现数据拼装逻辑。

## 2. 评测题库页（`eval-cases.vue`）

- [x] 2.1 回退改 `WorkbenchCrumbs`（平台助手 / 评测 / 评测题库，返回芯片在右端），页面动作从 `.doc-body` 顶层移入工具条。验证：页面 DOM 里 `.doc-body` 的直接子元素不再包含按钮；`npm run lint:styles` 通过。
- [x] 2.2 表纸概览：用 `AppTable`（带 `accent`）列出题目 / 步数 / 操作，标题行带总数与「新建题目」。验证：有数据时每行一题、行内有编辑与删除；`npm run typecheck` 通过。
- [x] 2.3 三态：`SkeletonCard` 加载、`EmptyState`（含「新建第一条」）、`ErrorState`；加载期间不得渲染空态。验证：断网/慢网下首次进入先见骨架；清空题库后见空态而非空白。
- [x] 2.4 编辑纸：`el-dialog` 内渲染题目 + 步骤（动作 / 断言 / 页面锚点），字段带可见 `label`，取消不发写请求。验证：点编辑弹层预填当前值；点取消后 `PATCH` 未发出（网络面板无请求）。
- [x] 2.5 保存写回：用 `PATCH /api/ai/eval-cases/{id}/` 返回的 `case` 替换数组内该项，不调 `load()`；失败保留编辑内容并提示原因。验证：改题目保存后仅该行变化、列表不重载；伪造 400 后弹层不关闭且保留输入。
- [x] 2.6 删除：`ConfirmButton`（`doodle` → 危险色）二次确认，取消不删、确认后移出并更新总数。验证：取消后行仍在且无删除请求；确认后行消失。
- [x] 2.7 补 `frontend/tests/ai-assistant/p0/eval-cases.spec.ts`：覆盖历史行/题目行构造与「编辑后只替换该行」的纯函数。验证：`npm run test -- eval-cases` 通过。

## 3. 评测页（`evals.vue`）

- [x] 3.1 回退改 `WorkbenchCrumbs`（平台助手 / 评测），「编辑题库」与「返回助手」并入面包屑行右端按钮组。验证：`.doc-body` 顶层无裸按钮；面包屑行右端有返回芯片。
- [x] 3.2 未选态：未选对象时只渲染对象类型切换、对象选择与一句引导，主按钮置灰；评分结果、真题集、历史与口径正文一律不渲染。验证：首次进入页面源里没有评分卡与真题表；选完对象后它们出现。
- [x] 3.3 状态条：`FilterTabs` 替代手写分段控件，对象与交接来源用 Element Plus 表单皮肤（带 label），右侧显示发布状态与最近分数。验证：页面上不再存在 `.eval-page__kinds` 与裸 `<select>`。
- [x] 3.4 三张 `.doc-section`（评分 / 真题集 / 历史）替代私有 `.eval-page__panel`，删除该容器样式。验证：`grep` 不到 `.eval-page__panel`；分区标题走 `.doc-section__title`。
- [x] 3.5 评分卡：两项指标各显示分数与理由，按档位取色，低于阈值带「未达 0.5」标识；`scoreTone` 低分档由 `--c-element` 改为 `--app-marker-red`，同步 `eval-view.spec.ts`。验证：`npm run test -- eval-view` 通过；低分卡边框为危险色。
- [x] 3.6 口径折叠区：默认收起，标题带指标数；展开后按指标分块、要点用列表，不再整段 `<pre>`。验证：默认渲染不含口径条目文本；展开后 3 块各列要点。
- [x] 3.7 历史表列语义：时间 / 指标与分数 / 提示词指纹（次要小字），分数列显示分数。验证：任一行分数位置不再出现指纹串。
- [x] 3.8 真题集：`AppTable` 列出题目 / 步数 / 步骤通过 / 耗时 / 判定（勾选走表格选择列），串号输入与「跑真题」进工具条，结果按明确判定色呈现。验证：跑一次真题后表格出现逐条结果；未勾选时按钮置灰。
- [x] 3.9 补 `frontend/tests/ai-assistant/p0/eval-view.spec.ts` 中的历史行构造与档位文案断言。验证：`npm run test -- eval-view` 通过。

## 4. 助手看板发布（`AssistantCard.vue` / `index.vue` / `SopWorkflowSection.vue`）

- [x] 4.1 `AssistantCard` 增 `canPublish` 输入：草稿卡在动作行下方加 1.5px 虚线分隔与第三个动作「发布」（`--c-case` 20%→5% 渐变，高度 ≤32px，带焦点环）；已发布卡不渲染。验证：`npm run lint:lines` 通过（虚线仍在白名单文件内）；草稿卡 DOM 出现发布键、已发布卡不出现。
- [x] 4.2 草稿标识迁移：从 `h3` 内联文本移到右上角独立胶囊，名称文本只含显示名。验证：`assistant-card.spec.ts` 中「名称元素文本」断言不再包含「草稿」，胶囊单独存在。
- [x] 4.3 移除卡片外的发布按钮（`index.vue` 与 `SopWorkflowSection.vue` 两处），改为向卡片传 `canPublish` 并监听卡片发出的 `publish` 事件。验证：页面 DOM 中发布按钮都在卡片内部；表格/网格里不再有兄弟按钮。
- [x] 4.4 发布失败隔离：把页面级 `error` 拆为「列表加载错误」与按 `assistant_id` 的 `publishError`，失败时该卡显示原因 + `ElMessage.error`，网格不消失；成功只替换该卡状态。验证：对未发布两侧名片的草稿工作流点发布，其余卡片仍在；成功发布后该卡发布键与草稿胶囊消失。
- [x] 4.5 同步 `frontend/tests/ai-assistant/p0/assistant-card.spec.ts`：动作列表改为「草稿三动作 / 已发布两动作」，并补「发布失败时卡片仍渲染」。验证：`npm run test -- assistant-card` 通过。

## 5. 文档与门禁

- [x] 5.1 更新 `.agents/docs/frontend/ai_assistant/ai_assistant_workbench_and_cards.md`：卡片动作改为「配置 / 对话（/ 草稿卡发布）」、草稿标识为独立胶囊、发布失败只影响该卡。验证：文档与代码一致（人工比对一次）。
- [x] 5.2 前端门禁：`npm run typecheck`、`npm run lint`、`npm run lint:styles`、`npm run lint:lines`、`npm run build`、`npm run test` 全部通过。验证：六条命令输出无错误。
- [x] 5.3 人工验收（1440px 与 1024px 两个宽度）：评测页无通栏动作条、未选对象只见引导、口径默认收起；题库页表纸 + 弹层编辑、删除二次确认；助手看板草稿卡发布键在卡内、发布失败不消失。验证：逐条对照 `specs/frontend-eval-pages` 与 `specs/ai-assistant-card` 的场景勾选。
- [x] 5.4 `openspec validate refine-eval-pages-ui --strict` 通过。验证：命令返回 valid。
