## Why

登录页仍是「居中拍立得大卡 + 表单与动物贴纸并排」，与 hand-drawn doodle showcase 的 Hero（左文案/双 CTA、右 Meeting doodle 钉板、横线笔记本底）不一致，品牌首屏观感落后于侧栏与主区已收敛的纸面语言。需要把 `/login` 对齐 showcase Hero，同时保留现有认证流程。

## What Changes

- 登录页背景改为横线笔记本纸面 + 稀疏 doodle（**仅 `/login` 页**，不改全站 L0 暖白实色口径）
- Hero 改为左右分栏：左侧标题「AI 自动化测试平台」+ 现有两行描述（`--app-font-brand`）+「登录」/「注册」双 CTA
- 右侧 Meeting doodle（虚线钉板）承载登录/注册输入区；钉板标题随模式为「登录」或「注册」
- Meeting doodle 内表单为**扁平字段**（无嵌套 `AppCard` / `.ac-card` / `el-card`）
- 点击左侧「登录」显示登录表单，点击「注册」显示注册表单（复用现有 `switchMode`）
- **移除**登录页右侧动物贴纸板（`AnimalFace` / `.hero__brand` 整块删除）
- 认证 API、表单校验、账号切换提示、错误遮罩行为保持不变

## 关联文档

- UI 参考：`temps/hand-drawn-doodle-showcase.html`（Hero + `#principles`）
- 主题约束：`.agents/skills/doodle-craft`（令牌唯一真相源 `tokens.css`；全站禁止横线本，本变更登记为登录页例外）
- 无新增 PRD/ARCH：纯前端登录壳层视觉与交互改版

## Capabilities

### New Capabilities

- `frontend-login-hand-drawn-hero`: `/login` 页 hand-drawn Hero 版式、横线纸面例外、Meeting doodle 表单容器、登录/注册 CTA 切换行为

### Modified Capabilities

- `frontend-l3-content-block`: 登录页认证区不再要求嵌套 `AppCard`；改由 Meeting doodle 直接承载扁平表单

## Impact

- 前端：`LoginView.vue` / `LoginView.style.css`；`LoginCard` / `RegisterCard` / `AccountSwitchPrompt` 去掉 `AppCard`；`views/styles/login-card.css` 改为扁平面板
- 测试：`frontend/tests/login/**`（贴纸板消失、CTA、Meeting 标题、无 `.ac-card` 嵌套）
- 后端 / API：无
- 全站 L0 / 侧栏 / 工作台背景：无改动
