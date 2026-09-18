## Why

L2 的**行为与作用域**已在上一个变更（`fix-l2-page-region`）收敛，但**结构形态**仍然分裂：页面根区存在 5 类实现，其中 7 个页面自建私有根与 `__body`/`__main`、完全不复用共享骨架；页头有 2 个共享组件并在同一模块内混用，导致从列表页点进详情页时页头形态整体跳变；页头与主体的水平内边距有 5 种取值（12/18/20/24/28px）；另有 3 处 L2 死代码。这些分裂使「改一次 L2 要改 N 处」，也无法从骨架类名推断结构——新人或 AI 接手时只能逐页目视。

## What Changes

- **P5 页面根区收敛到共享骨架**：7 个页面（case-manager ×3、element-locator ×3、workflow 原型列表 ×1）的页面根迁到 `.doc-page`（+ `.doc-page--fixed`），主体容器改用 `.doc-body`；模块私有类降级为作用域 modifier（与 `dashboard` 根上的 `device-workbench` 写法一致），点阵底纹、分隔线、树面板与表格布局等观感保持不变。
- **P6 页头收敛到单一共享件**：report-generator 3 个详情页（`/reports/{runId}`、`/reports/cases/{type}`、`/reports/task/{id}`）的页头从 `PageHeader` 换成 `WorkbenchHeader`，与同模块列表页一致；删除 `shared/components/PageHeader.vue`，同步 `frontend/AGENTS.md` 的共享件清单。
- **P7 清理 L2 死代码**：删除 `WorkbenchHeader` 的 `mark` prop 与 emoji 回退分支（无任何调用方传值）；删除无 CSS 规则消费的 `.detail-page` 标记类；report-generator 未被 import 的 `PAGE_HEADER` 常量改为被列表页消费（补齐 `icon`/`iconGradient`），消除模板中的标题/副标题/图标硬编码。
- **P8 水平内边距统一到 `var(--app-space-lg)`（24px）**：全局 `--fixed .doc-body` 的 18px、report-generator 列表的 20px、ai-assistant 的 20px、device-inspector 的 28px、CaseFileSheet 的 12px 各自归位到 24px；页头保持 24px 不动。
- **BREAKING**：无接口/协议变化。**但 P6 会改变上述 3 个 report 详情页的页头外观**（白色 Hero 卡 → 96px 通栏），已在开工决策中确认。
- **不改**：L0/L1 骨架与滚动策略（report 详情页仍为策略①）、API 契约、路由表、后端、点阵纹理归属。

## 关联文档

- `openspec/specs/frontend-l2-page-region/spec.md`：本次是在其既有 5 条行为契约之上补 4 条结构契约
- `frontend/AGENTS.md`：L0–L5 区域模型与归属、`shared/` 共享件清单（P6 需同步其第 8 项）
- `dev_docs/05-开发与测试/设计方案与报告/报告-前端区域层级与L2现状复盘.html`：P5–P8 的问题来源与量化依据
- `.agents/skills/doodle-craft/references/tokens.md` 与 `components.md`：令牌口径与组件规格
- 说明：`dev_docs/文档编号对照表.md` 不存在，`dev_docs/05-开发与测试` 下只有 API/测试类文档、无 UI 规范编号文档，故不引用编号文档（沿用前两个前端变更的先例）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l2-page-region`: 在既有 5 条行为契约（按钮语义色 / 不覆盖正文 / 层叠生效 / 主题作用域 / L0-L1 契约不变）之上，**新增 4 条结构契约**——页面根复用共享骨架、页头由单一共享件提供、页头与内容共用同一水平内边距、L2 不留无消费方声明；既有 5 条行为不变。

## Impact

- **P5**：`frontend/src/modules/case-manager/{ProjectList,ProjectWorkspace,CaseFileSheet}.vue`、`frontend/src/modules/element-locator/{ProjectList,ProjectWorkspace,LocatorFileView}.vue`、`frontend/src/modules/workflow/PrototypeList.vue`
- **P6**：`frontend/src/modules/report-generator/{CaseBreakdown,TaskReport,ReportDetail}.vue`、删除 `frontend/src/shared/components/PageHeader.vue`、同步 `frontend/AGENTS.md`
- **P7**：`frontend/src/shared/components/WorkbenchHeader.vue`、`frontend/src/modules/report-generator/{index.vue,constants.ts}`
- **P8**：`frontend/src/style.css`、`frontend/src/modules/device-inspector/index.vue`、`frontend/src/modules/ai-assistant/index.style.css`、`frontend/src/modules/report-generator/index.vue`、`frontend/src/modules/case-manager/CaseFileSheet.vue`
- **测试范围**：`frontend/tests/`（若有 PageHeader 或骨架类断言需同步）、`cd frontend && npm run typecheck`、`vue-frontend-check` 前端门禁、浏览器回归（21 个页面 × 768/1024/1280 三档）
- **不影响**：后端 `apps/`、API 契约与信封、鉴权、路由表、L0/L1 骨架、各模块业务数据流
