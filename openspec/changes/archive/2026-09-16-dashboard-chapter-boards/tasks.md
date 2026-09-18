## 1. 结构重组

- [x] 1.1 将 `index.vue` 六个 `.doc-section` 收束为四章节（运营 / AI / 资产 / 趋势动态），用例与元素合并为资产章双栏，并在浏览器中确认四章顺序与标题
- [x] 1.2 为每章补齐章节头（方标、eyebrow、marker 标题）与 chip 摘要；AI 分角色灰字改为 chip，目视确认无「分角色 Token（累计/今日）」裸灰字行

## 2. 样式

- [x] 2.1 更新 `DashboardView.style.css`：章节钉板（虚线边、硬阴影、微倾）、chip、subhead、asset-cols；去掉「清新简洁风」与扁平 section 冲突规则；`npm run typecheck`（或项目等价命令）通过
- [x] 2.2 颜色/间距使用 `var(--*)`，无新增硬编码色（ECharts 除外）；对照 doodle-craft 自检项目视过关

## 3. 回归

- [x] 3.1 跑仪表盘相关前端测试（`npm test` 限定 dashboard）并修复因 DOM 结构调整的断言
- [ ] 3.2 本地打开 `/dashboard` 目视：四章钉板、资产双栏、趋势+动态同章、页脚仍在；确认未改 API 请求路径
