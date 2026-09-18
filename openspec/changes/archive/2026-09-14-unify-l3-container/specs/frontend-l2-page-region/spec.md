## MODIFIED Requirements

### Requirement: L2 page roots reuse the shared page skeleton
前端每个 L2 页面根 SHALL 复用共享骨架类作为唯一页面根容器（`.doc-page`；固定视口页同时带 `.doc-page--fixed`），其主体内容容器 SHALL 复用 `.doc-body`；模块 MUST NOT 以私有类名自建等价于该骨架的根容器或主体容器，私有类只能作为作用域 modifier 与既有样式钩子保留。主体为自由布局画布 / 图形编辑器的页面 MAY 例外使用私有主体容器，但该例外 MUST 同时登记在 `frontend/AGENTS.md` 与本 spec，且 MUST NOT 扩散到非画布页面。

#### Scenario: Case and element pages use the shared skeleton
- **WHEN** 依次打开 `/cases`、`/cases/projects/:projectId`、`/cases/projects/:projectId/files/:fileId`、`/elements`、`/elements/projects/:code`、`/elements/projects/:code/files/:fileId` 与 `/workflow`
- **THEN** 每个页面根元素的 class 同时包含 `doc-page` 与 `doc-page--fixed`，且其主体内容容器包含 `doc-body`

#### Scenario: Visual appearance does not regress
- **WHEN** 对比迁移前后上述 7 个页面
- **THEN** 分隔线、树面板宽度与表格横向滚动行为保持等价，无新增重叠或内容裁剪（纸面点阵已按 `frontend-l3-container` 收敛为暖白实色 + 主区涂鸦）

#### Scenario: Canvas page exception is registered and contained
- **WHEN** 检查 `/workflow/prototypes/:prototypeId` 的主体容器
- **THEN** 它是 `.wb-body` 且该例外在 `frontend/AGENTS.md` 与本 spec 中均有登记；其余模块页面主体仍为 `.doc-body`
