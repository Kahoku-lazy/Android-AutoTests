# 文档索引门户 · 静态资源

从 `index.html` 拆出，避免单文件过大。

| 文件 | 职责 |
|------|------|
| `doc-portal.css` | 门户样式（侧栏、卡片、Stage 色调、AI 工作流） |
| `stages-data.js` | `STAGE_COLORS` + `STAGES` 阶段索引数据 |
| `doc-portal.js` | 渲染、图表、路由 |
| `workflow-panel.js` | AI 工作流面板 HTML（`WORKFLOW_PANEL_HTML`） |

打开方式：仍双击 / 用浏览器打开上级目录的 `index.html`（相对路径引用本目录）。
