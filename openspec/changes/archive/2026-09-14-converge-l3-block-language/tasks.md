## 1. 判定表

- [x] 1.1 产出逐页判定表（11 处顶层块 + 8 个 AppCard 消费文件），逐条标注角色（页面级分区 / 数据块 / 认证卡 / 条目卡）与是否合规；验证：表覆盖全部 `.doc-section` 与 `AppCard` 消费文件，无遗漏，且结论为「无迁移项」

## 2. 文档口径修正

- [x] 2.1 修正 `frontend/AGENTS.md` AppCard 段的判据：由单口径「把一组内容框成『块』就用它」改为二分「页面级分区 → `.doc-section`；可复用数据块 → AppCard」，保留「单条数据的卡片用模块私有组件」与「认证卡」场景；验证：`rg -n "把一组内容框成" frontend/AGENTS.md` 0 命中，且两种角色表述齐全
- [x] 2.2 在 AppCard 段补写主题作用域前提（外观仅 `.wb-shell` / `.workflow-workbench` 内生效）；验证：文档含该前提且与 `workbench-theme.css` 事实一致

## 3. 静态核验

- [x] 3.1 按 spec 的 4 条 Scenario 逐条核验：顶层分区均为 `.doc-section`、数据块均为 `.ac-card`、登录页认证卡保持 `.ac-card`、无「`AppCard` 包 `.doc-section`」的反向嵌套；验证：核验记录逐条通过（可用 grep 定位顶层块 + 人工确认嵌套关系）

## 4. 门禁

- [x] 4.1 运行 `cd frontend && npm run typecheck`；验证：与变更前一致（本变更零代码改动，不应引入或消除任何错误）
- [x] 4.2 构建校验 `npx vite build --mode development`；验证：构建成功
- [x] 4.3 用 `vue-frontend-check` 技能过一遍前端门禁；验证：无新增违规（本变更仅文档与 spec）
