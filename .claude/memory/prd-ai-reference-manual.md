---
name: prd-ai-reference-manual
description: PRD 提炼为 AI 编码速查手册 — 从 11 份 PRD 文档提取数据契约/状态机/约束清单/错误模板/陷阱/Non-goals
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

`dev_docs/02-PRD需求/AI编程参考手册.md` 是从全部 11 份 PRD 文档提炼的单文件 AI 编码速查手册，结构化 10 个章节。

**Why:** 原始 PRD 文件数量多（1 总 + 7 子 + 2 工作流 + README）、格式混杂（MD + HTML）、含大量人类阅读叙事内容。AI 需要的是：跨模块数据契约、状态机转换规则、约束清单、错误处理模板、已知陷阱、Non-goals。

**How to apply:** AI 做本项目的编码工作前应先读此手册。遇到不一致时按手册第十章优先级取信（代码 > HTML 规格 > 手册 > 子 PRD > 总 PRD）。

手册路径：`dev_docs/02-PRD需求/AI编程参考手册.md`
