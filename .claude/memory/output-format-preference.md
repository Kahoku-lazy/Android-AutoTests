---
name: output-format-preference
description: 用户偏好：方案文档、分析报告等输出 HTML 格式而非纯 Markdown
metadata: 
  node_type: memory
  type: user
  originSessionId: b8f7928d-d4e9-48a7-8c9a-9c28f64920f8
---

用户要求后续方案文档、分析报告、流程文档等都输出 HTML 格式（在 Markdown 之外额外生成 HTML）。

HTML 报告应放在对应模块的 `tests/functional/{module}/reports/` 目录下，风格匹配项目 animal-island 暖木色主题。

**Why:** 用户希望可视化程度更高的输出格式，方便查看和分享。

**How to apply:** 每次产出方案/分析/流程类文档时，在写完 Markdown 后额外调用 Write 生成 HTML 版本。使用项目中已有的 HTML 报告风格（暖木色配色、SVG 图表、卡片布局）。
