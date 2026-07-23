# CLAUDE.md — 前端主题修改

## 工作流

1. **先出原型，再写代码** — 改任何模块主题前，先出 3 个概念原型让用户选。用户选定后再实施方案。
2. **先 Glob 再动手** — 选定方向后，列出模块下所有文件，逐个 Read 每个组件的 `<style>` 块。
3. **改完 grep 残留** — 搜旧令牌/旧色值/旧效果关键词，必须返回 0 行。
4. **只改 CSS，不改逻辑** — 不碰 props/emits/API/路由/动画。

## 设计系统

> 完整规范 → [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)

核心要点速查：

| 要素 | 规格 |
|------|------|
| 主色 | `#2d2d2d` 墨色 / `#999` 弱化 / `#fefcf6` 纸底 |
| 边框 | `2.5px solid #2d2d2d`（外框）、`1.5px`（分隔） |
| 圆角 | `6px 10px 6px 10px`（卡片）、`4px 8px`（按钮） |
| 字体 | `Caveat`（标题）、`JetBrains Mono`（代码）、`Inter`（正文） |
| 卡片 | 白底 + 图钉 `::before` + 微旋转 + hover 归正 |
| 页脚 | 黄色便签 `#FFE066`，字色 `#5a4e20` |
| 背景 | dot pattern `radial-gradient(#d4cdc0 0.8px, transparent)` on `#fefcf6` |
| 色值 | 全部从 `tokens.css` 取，禁止组件内硬编码。**Canvas/ECharts JS 配置必须用字面量** |
| 模块色 | dashboard:yellow / device-pool:green / element-locator:purple / case-manager:teal / test-runner:pink / report:brown / ai:orange / workflow:blue |
