---
name: css-debug-workflow
description: CSS 布局问题排查的三步铁律
metadata: 
  node_type: memory
  type: feedback
  project: project
  originSessionId: 805625f3-de5d-44bb-82e8-2dd173acf307
---

# CSS 布局问题排查三步铁律

**Why:** 元素管理页 UI 问题反复修了三轮才彻底解决。根因不是技术难度，而是每次跳过关键步骤、凭猜测写 CSS。

**How to apply:** 每次遇到"区域空白/溢出/看不到"类问题时，严格执行以下三步，不跳过任何一步：

## 第一步：查 DOM（不可跳过）

```bash
# 浏览器 DevTools → Elements → 找到目标元素 → 看：
# 1. 实际的 class 名是什么？（animal-island-vue 用 BEM 双下划线：.animal-tabs__list，不是 .animal-tabs-list）
# 2. 组件内部嵌套结构是什么？（Card 没有 .animal-card-body 和 .animal-card__content）
# 3. CSS 选择器是否匹配到了目标元素？（Computed 面板看哪些规则生效）
```

**铁律：不要猜 animal-island-vue 组件的内部类名。必须 DevTools 确认。**

## 第二步：画高度链（不可跳过）

从 `<html>` 到目标元素，逐层检查 flex/grid 容器：
- `flex: 1` 的父级有没有 `min-height: 0`？
- `overflow: auto/hidden` 在哪一层？（只能有一层负责滚动）
- 整个链是否从 `100vh` 一路畅通到底？

**铁律：用纸或注释画出完整高度链路，标出每个节点的 flex/min-height/overflow。**

## 第三步：选滚动策略（二选一，不能混）

| 策略 A | 策略 B |
|--------|--------|
| 视口固定 + 内部区域滚动 | 内容撑开 + 页面整体滚动 |
| `100vh` → flex 链 → 最内层 `overflow: auto` | 根节点 `min-height: 100%`，中间不用 `overflow: hidden` |
| 适合：表格、侧边栏、固定工具栏 | 适合：表单、卡片列表、内容为主 |
| 需完整高度链 | 需去掉中间层的 `overflow` 限制 |

**铁律：先问用户期望什么行为，再选策略。一旦选定，全局一致，不要混用。**

## 不要做的事

- ❌ 凭记忆写 animal-island-vue 组件的内部 class 名
- ❌ 发现滚动不生效就一层层加 `overflow: hidden`（越加越碎）
- ❌ 不看已有正确实现（如 test-runner 的布局）闷头自己试
- ❌ 用 curl/grep/vite build 验证 CSS 问题（CSS 只活在浏览器里）
- ❌ 高度链断了不溯源，只修最外层或最内层

## 正确流程速查

```
用户报告 UI 异常
  → DevTools 查 DOM：元素存在吗？class 正确吗？
  → Computed 面板：高度/overflow/flex 生效值是什么？来源文件是哪个？
  → 画高度链：从 viewport 到目标元素，逐层标注
  → 选策略：锁视口 or 撑页面？
  → 一次改对，浏览器验证
```

## 关联

- [[css-flex-direction-debug]] — flex-direction 被全局样式覆盖导致左右变上下
- [[animal-island-ui-api-traps]] — animal-island-vue 组件 API 与 Element Plus 差异
