---
name: doc-mgmt-consolidate-root-docs
description: 散落文档统一迁入 dev_docs；不留软链，只认新路径
type: project
---

约定（2026-07-10 严格版）：

- 管理/设计/开发/测试复盘文档只在 `dev_docs/`。
- **禁止**根目录或旧目录软链兼容；路径变更后同步更新 README/AGENTS/Agent 提示词/索引内引用。
- 已删除：`01-技术架构/`、`03-产品原型/`、`04-测试方案/`、`diagrams/`、`02-PRD需求/子PRD/`。
- TREP 真相：`04-任务拆分/架构师-详细任务计划-TREP-v1.0-protocol.html`。
- animal-island 提示词：`03-设计与架构/技术栈-PROMPT-animal-island-ui一键提示词.md`。
