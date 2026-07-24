# CLAUDE.md — 前端

## 主题

平台当前使用 **Doodle Craft** 主题。修改任何视觉样式前必须先阅读主题规范：

→ `frontend/THEME.md`

## 修改铁律

1. **先出原型，再写代码** — 改任何模块前先出 3 个 HTML 概念原型
2. **先 Glob 再动手** — 列出模块下所有 `.vue`，逐个 Read 每个 `<style>` 块
3. **改完 grep 残留** — `grep -rn "backdrop-filter\|app-glass"` 必须返回 0
4. **只改 CSS，不改逻辑** — 不碰 props/emits/API/路由/动画
