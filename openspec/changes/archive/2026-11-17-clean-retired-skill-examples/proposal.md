## Why

页面流（remove-page-flow-module）与元素定位（retire-inspector-and-element-locator）已退役，但 doodle-craft 与 frontend-change-plan 两个技能文档仍把它们当作现存模块举例（SketchCard 消费方列举、原型模板的「Hub→画布」示例段）。AI 加载这些技能做 UI 方案时会被误导，给不存在的模块套组件或版式。这是退役单 tasks 6.4 记录的文档残留项。

## What Changes

- **doodle-craft**：[SKILL.md](../../../.agents/skills/doodle-craft/SKILL.md) 选型表「资源入口卡（用例 / 元素 / 页面流）」与 [cards.md](../../../.agents/skills/doodle-craft/references/components/cards.md) SketchCard 用途列举，去掉已退役的「元素 / 页面流」，保留用例。
- **frontend-change-plan 原型模板**：删除页面流模块深度表行、「页面流 · Hub → 画布」迷你原型段（HTML + 配套 `/* Workflow */` JS）、版式 C/H 描述、P2 落地行、导航①描述、matrix 标题与 lead 中的页面流举例（同句的元素举例一并清）。
- 保留通用版式规则（如「画布 / 表体 / Excel 禁止旋转」）与 CSS 调色板——非页面流专属举例。

## 关联文档

无 PRD 需求编号：remove-page-flow-module 退役的文档残留清理。纯技能文档同步，无平台规格行为变化，故 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无（skip_specs: true —— 技能指引文档不承载平台行为规格）。

## Impact

- `.agents/skills/doodle-craft/SKILL.md`（带并行未提交改动，部分暂存避开并行 hunk）
- `.agents/skills/doodle-craft/references/components/cards.md`（干净）
- `.agents/skills/frontend-change-plan/assets/plan-prototype-template.html`（干净）
- **Non-Goals**：不改平台代码/主规格；不动 doodle-craft 并行迭代中的其它内容；通用版式规则与 CSS 保留。
