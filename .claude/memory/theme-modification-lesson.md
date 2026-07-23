---
name: theme-modification-lesson
description: "前端多文件修改时，必须先 Glob 探索组件树再逐个覆盖，不能假设\"改了一个文件就够了\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0e14561-20d7-4f7c-b951-7b56274cf187
  modified: 2026-07-23T12:11:54.560Z
---

修改前端模块视觉风格时，单文件替换策略不可靠——侧边栏是单文件组件所以一次成功，但仪表盘是 7 个子组件组合，只改 index.vue + 2 个直接引用组件，漏了 5 个深层子组件。

**Why:** Vue scoped style 是视觉隔离边界，每个 `components/*.vue` 都有独立的 style 块需要单独覆盖。不先 Glob 绘制完整组件树就无法确保全覆盖。

**How to apply:** 改任何模块的主题/样式前，先 Glob → 逐个 Read style 块 → grep 旧令牌残留 → 构建验证。流程不因目标看起来简单而省略。

[[frontend-workflow]]
