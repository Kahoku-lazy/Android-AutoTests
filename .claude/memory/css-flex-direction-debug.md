---
name: css-flex-direction-debug
description: 页面区域空白/不显示的 CSS 排查流程
metadata: 
  node_type: memory
  type: project
  originSessionId: b05814f4-5f5d-4bc7-9238-26a81baf151e
---

收到"XX 区域空白/没有内容/右侧不显示"类反馈时，**必须先打开浏览器 DevTools 检查 CSS computed styles**，而不是反复改模板结构或数 v-if/v-else 闭合。

标准排查流程：
1. DevTools Elements → 目标 DOM 是否存在？不存在 = 模板/JS 问题；存在 = CSS 问题
2. DevTools Computed → 检查 display / width / height / flex-direction / overflow
3. 特别注意全局 CSS 继承冲突（如 `.doc-body` 的 `flex-direction: column` 覆盖子组件期望的横向布局）
4. scoped 样式内看不出全局冲突——必须看浏览器 computed 面板的**来源文件**列

**Why:** 2026-07-06 case-manager 右侧空白排查耗时超过 1 小时，反复重写模板、数标签闭合、curl API，最终根因是全局 `.doc-body { flex-direction: column }` 与 `.case-layout { display: flex }` 冲突。vite build / curl / 模块 HTTP 200 全部正常，纯 CSS 问题不会被任何 CLI 工具捕获。

**How to apply:** 收到视觉问题反馈 → 第一步打开浏览器 DevTools，不碰代码。确认 computed styles 无误后再排查模板逻辑。详见 [[frontend-rules]] §页面区域空白/不可见排查流程。
