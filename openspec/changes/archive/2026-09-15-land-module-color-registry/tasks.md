## 1. 共享令牌层（必须先做，所有模块依赖其词汇）

- [x] 1.1 `--ai-*`（35 个）从 `:root` 迁入既有 `.ai-workbench` 作用域块；验证：`:root` 内 `--ai-` 命中 0，作用域块内 35 条声明齐全（`tokens.css` 267–310 行区间）
- [x] 1.2 `--case-*`（2 个）迁入新增 `.case-workbench` 作用域块，并给 case-manager 3 个页面根加类；验证：`:root` 内 `--case-` 命中 0；`ProjectList.vue` / `ProjectWorkspace.vue` / `CaseFileSheet.vue` 页面根均含 `case-workbench`
- [x] 1.3 退役 `--doodle-*`：`--doodle-bg`→`--paper`（同值）· `--doodle-ink`→`--ink` · `--doodle-radius` 转正为 `--app-radius-table` · `--doodle-shadow`→`--app-shadow-sm`，4 条声明删除；验证：全仓 `var(--doodle-` 命中 0
- [x] 1.4 收敛并删除 `@deprecated` 6 条别名声明与用法（`--app-ink-muted`→`--app-text-secondary`【#999 同值】· `--app-ink`→`--ink` · `--app-accent-blue`/`--app-green`→`--c-workflow` · `--app-blue`→`--c-element` · `--app-accent-purple`→`--app-status-purple`）；验证：全仓 `var(--app-(ink|ink-muted|green|blue|accent-*)` 命中 0，`tokens.css` `@deprecated` 段改为迁移说明
  - 途中修正主审自身错误：初稿把 `--app-ink-muted`(#999) 误映射为 `--app-text-muted`(#bbb)，已向 5 个在跑分片发更正并用 git-diff 行定位修正已完成模块 33 行（`--app-ink-muted` 归零；未误伤文件原生的 `var(--app-text-muted)`，如 `CaseBreakdown.vue:464`）
- [x] 1.5 `device-pool/components/NetworkConnectDialog.vue` 的 `var(--ai-bg-neutral)` → `var(--app-bg-subtle)`；另修共享件反向借用 `DoodleNote.vue` 的 `var(--ai-sticky-bg)` → `var(--paper)`；验证：`var(--ai-` 消费只在 ai-assistant 模块内
- [x] 1.6 作用域可达性复核：`--ai-*` 消费集中在 4 个带 `.ai-workbench` 的 AI 页面内；`.section-block`（`StepScreenshotPanel.vue:64`）包住消费其分类色板的徽标（:94）；EP 2.7 `el-dialog` 为 `Teleport({ disabled: !appendToBody })` 且仓库 `append-to-body` 命中 0 → 弹层原地渲染；Teleport 目标（workflow 的 `.wf-ctx`/`.el-picker` 等）的变量均声明在元素自身类上

## 2. 各模块色值登记（8 模块 + 共享件层，并行分片）

- [x] 2.1 CSS 侧未登记字面量归零：9 个分片（8 模块 + `shared/{components,styles}`）完成「同值令牌替换 / 就近具名声明」；验证：全仓 CSS 侧未登记裸 hex = **0**、裸 rgba/hsl = **0**（脚本按「值已在 tokens.css 登记 / 落在自定义属性声明段内」二分判定），登记载体 357 行
- [x] 2.2 script/.ts 侧画布色集中：report-generator 轴/滑块色 → `CHART_COLORS.axis`（2 组件 5 处）；workflow HTTP 方法色 → `nodeRegistry.METHOD_COLORS`（`PageFlowNode` 与 `NodeContextMenu` 副本合一）；验证：方法色字面量只存在于 `nodeRegistry.ts` 声明处，轴色只存在于 `constants.ts`
- [x] 2.3 各模块同步完成 1.4 的别名替换分片；验证：各分片验收 1 均 0 命中（含 case-manager 报告本模块无该别名、device-inspector/ai-assistant 按更正落 `--app-text-secondary`）

## 3. 规格与文档同步

- [x] 3.1 本变更 spec 追加 2 条需求 / 6 场景（色值登记处归属 · 模块令牌家族作用域含 Teleport 逃逸口）；验证：`openspec validate --strict` 通过
- [x] 3.2 `frontend/AGENTS.md`：L0 §②（tokens.css 结构含模块作用域段）· §③.4（模块家族不在 `:root`）· §④.3（改写为可执行口径 + EP Teleport 证据 + 禁止跨模块借用）· §⑥（新增静态判据）；L4 §③ 新增第 7 条（图表/canvas 色集中登记）；验证：速查与 spec 一致，`:root` 口径不再自相矛盾
- [x] 3.3 设计文档复盘章节回写：判定卡「主题令牌体系」由「方向对齐 · 落地不齐」更新为「已落地」；「未收敛观察项」重写为「本轮收敛」+「剩余观察项」（含新发现的节点渲染色漂移、方法色覆盖不一致、`--case-z-context` 悬空变量）；footer 补第二次变更；验证：章节内不再把已收敛项列为观察项

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：`TOTAL_ERRORS = 34`（与基线一致，0 新增），其中应用代码 `APP_CODE_ERRORS = 0`（34 条全在既有 `tests/`）
- [x] 4.2 用 `vue-frontend-check` 过改动文件（calibration §7 强制扫描 + 逐模块验收 + 全仓归零复核）；验证：分片自测与主审全仓复核一致；上轮回写的 5 类量规中「平行色板」「分类色板散落」「`:root` 模块变量」「废弃别名」四类已归零，「圆角字面量」仍为登记观察项
- [x] 4.3 `openspec validate --strict` 通过后经 `openspec-archive-change` 归档；验证：`frontend-l0-design-tokens` 规格含 3 条需求 / 11 场景，变更进入 archive
