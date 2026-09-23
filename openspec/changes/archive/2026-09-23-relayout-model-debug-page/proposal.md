## Why

「模型调试」页（/ai-assistant/toolbox/models/:role）第一版把**六个等权重面板**竖着堆在一起：角色概览 + 提示词 + 工具 + Skill + 知识库 + 对话。后果是读出"没有层级"——读者不知道先看哪块；对话被压在提示词（1,205 字整篇铺开）之后要滚四屏；工具平铺一列（执行模型 14 个）没有分组；Skill / 知识库的无序列表也看不出与"三模型共用 / 未挂 RAG"的关系。

已确认的可点方案：temps/relayout-model-debug-page-proto.html（左配置 / 右对话，变体 C 分栏台）。

## What Changes

- **三层语义重排**：角色带（当前是谁：角色分段 Tab + 模型名 / provider / 模态 / 连接态 + 工具·Skill·知识库计数）→ 生效装配（工具、Skill）→ 参考数据（知识库）+ 提示词（默认折叠）。
- **对话独立右栏常驻**：滚动只发生在消息区内部（MUST NOT 需要滚过提示词才能发问）。
- **工具按分类分组**：组头显示"该分类 N/M 启用"；条目保留 只读/写 与 已启用/已停用 徽标（分类数据后端已回，纯前端分组）。
- **提示词默认折叠**：头部显示字数与"库中当前值"来源标识，展开才渲染 Markdown。
- **两条归属标注升为组头徽标**：Skill「三模型共用」、知识库「执行链路未挂 RAG」。
- **角色切换为页内分段 Tab**：切角色走同一路由的 role 参数（MUST NOT 产生新的历史层级），页头返回与面包屑不变。
- **零后端改动**：接口 / 字段 / 权限 / 超时 5 分钟 / 不落库 / 不挂工具全部不动；不新增共享件（复用 WorkbenchHeader / WorkbenchCrumbs / 现有令牌）。
- **不**改装配台来源卡片与平台工具调试页；**不**"顺手"修其它页面。

## 关联文档

- PRD-需求总纲（AI 助手条目）
- 前置变更：add-model-debug-console（本单只改其页面版式；该变更需先归档，本单的 delta 才能并入同一能力主规格）
- 方案依据：temps/relayout-model-debug-page-proto.html（自包含方案 + 可点原型）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- ai-model-debug: 新增「调试页按三层组织并分组展示」要求——三层语义、对话常驻右栏、工具按分类分组且组头带 N/M、提示词默认折叠带字数与来源、归属标注为组头徽标、角色切换为页内 Tab。既有行为需求（配置读取 / 对话 / 权限 / 超时 / 不落库 / 不挂工具）不变。

## Impact

- 前端（唯一改动面）：frontend/src/modules/ai-assistant/ModelDebugPage.vue、ModelDebugPage.style.css；必要时新增 1 个私有子组件（若页面超 500 行）。
- 测试：frontend/tests/ai-assistant/p0/useModelDebug.spec.ts 增/改断言（三层结构、分组组头、提示词默认折叠、两条标注、角色 Tab 为链接）。
- 文档：无接口文档改动（零后端改动）；方案 HTML 作为设计依据。
- 后端 / 路由 / 迁移 / 依赖：无。
