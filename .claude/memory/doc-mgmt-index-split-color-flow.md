---
name: doc-mgmt-index-split-color-flow
description: index 拆分为 assets；智能体设计页多彩流程图风格
type: project
---

`dev_docs/`（2026-07-10）：

1. **index 拆分**：`index.html` 仅壳（~70 行）+ `assets/doc-portal.css` + `stages-data.js` + `doc-portal.js` + `workflow-panel.js`。
2. **多彩流程图**：`00-智能体/智能体体系设计.html` 采用参考图风格——彩色描边步骤条、双栏工具链/规则、三道防火墙虚线卡、API Key 生命周期。
3. 打开仍用上级 `index.html`（相对路径）；勿只开 assets 下单文件当门户。
---
