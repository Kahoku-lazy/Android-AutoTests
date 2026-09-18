## Context

动机见 `proposal.md` - Why。

现状（代码事实）：
- `LoginView.vue`：居中 `.hero__content` 大卡；`viewState` 驱动 `LoginCard` / `RegisterCard` / `AccountSwitchPrompt`；右侧 `.hero__brand` 动物贴纸板
- `LoginView.style.css`：点阵纸纹 + 实线边框拍立得壳 + 胶带伪元素
- 逻辑层 `LoginView.logic.ts` + `useViewStateMachine` 已提供 `switchMode('login'|'register')`
- 视觉参考：`temps/hand-drawn-doodle-showcase.html` Hero（`.hero` 双栏、`.btn-primary`/`.btn-ghost`、`.sketch-card.main` Meeting doodle）与 `#principles`
- 约束：`doodle-craft` 全站禁止横线本；本设计将横线本限定为登录页 scoped 例外，不改 `tokens.css` 的 L0 `--paper` 语义

## Goals / Non-Goals

**Goals:**
- 把登录壳层版式对齐 showcase Hero（背景、分栏、CTA、Meeting doodle）
- 复用现有认证 composable 与表单组件，零 API 变更
- 整块移除动物贴纸

**Non-Goals:**
- 不改注册/登录字段校验规则与后端契约
- 不改全站 `PaperDoodles` / L0 背景
- 不重做 `AccountSwitchPrompt` / `LoginErrorOverlay` 视觉体系（仅保证在新壳层内可显）
- 不引入新字体依赖（描述继续 `--app-font-brand`）

## Decisions

### D1 · 版式：左文案/CTA + 右 Meeting doodle
- **选择**：`LoginView` 模板改为 showcase 式 grid 双栏；表单迁入右侧钉板；去掉居中拍立得大卡外壳与动物贴纸。
- **备选**：仅换背景保留现布局 → 无法满足「表单进 Meeting doodle + 左 CTA」；完整复制 showcase HTML 为独立页 → 与现有 Vue 认证栈割裂。
- **理由**：需求直接指向 Hero 结构；认证逻辑已有 `switchMode`，改壳不改芯。

### D2 · 横线本仅 scoped 于 `.login-page`
- **选择**：在 `LoginView.style.css` 用 `repeating-linear-gradient` + `var(--paper)` 实现横线本；doodle 用页面内轻量 SVG/`aria-hidden` 层（可借鉴 showcase `.page-doodles`，不复用主区 `PaperDoodles` 以免与全站水印语义混淆）。
- **备选**：改全局 `--paper` / L0 → 违反已归档的全站暖白口径。
- **理由**：proposal 明确「仅登录页例外」。

### D3 · CTA 驱动模式，表单组件保留但去 AppCard 壳
- **选择**：左侧「登录」「注册」调用既有 `switchMode`；Meeting 标题绑定 `viewState`；`LoginCard`/`RegisterCard`/`AccountSwitchPrompt` 仍负责字段与提交，但根节点改为扁平 `.auth-panel`（无 `AppCard` / `el-card`），直接铺在 Meeting doodle 内。卡内「去注册 / 去登录」链接保留为次要入口。
- **备选**：保留 AppCard 嵌套 → 双层钉板/便签，用户已明确抛弃；把字段内联进 `LoginView` → 破坏现有组件与 testid 边界。
- **理由**：消除多层嵌套；组件职责与 testid 不变。

### D4 · 按钮皮肤用令牌映射 showcase 口径
- **选择**：主按钮对齐 showcase primary（实心强调色 + 墨色硬偏移阴影 + 粗实线边）；次按钮 ghost（透明底 + 虚线边）。颜色优先 `var(--*)`（如既有珊瑚/红强调令牌与 `--ink`），禁止在新 CSS 中扩散无关硬编码色。
- **备选**：直接复用 Element Plus `type=primary` 默认皮肤 → 与 showcase 硬阴影/虚线边不一致。
- **理由**：满足 doodle-craft「令牌不硬编码」与 showcase 观感。

### D5 · 动物贴纸整块删除
- **选择**：删除 `.hero__brand` 模板与相关样式及 `AnimalFace` 在登录页的引用。
- **备选**：缩成装饰 → 用户已明确「整块去掉」。

## 模块防火墙自检

- 跨 App import：无（纯前端 `views/`）
- 禁止跨 App import service/runner/consumer/state_machine：不涉及
- INSERT/UPDATE/DELETE 收敛 api.py：不涉及
- 前端不直连数据库：不涉及
- 无新跨模块依赖

## Risks / Trade-offs

- [登录页横线本 vs 全站禁止横线本] → 在 spec 中登记「仅 `/login`」例外；样式 scoped 到 `.login-page`；关单时用 vue-frontend-check / 目视确认主区无泄漏
- [卡内切换链接与左 CTA 并存可能显得重复] → 保留但样式弱化；不删 testid
- [窄屏双栏挤压] → CSS 在 ≤768px 改为单栏（上文案、下 Meeting），与现登录页响应式策略一致
- [AccountSwitchPrompt 占位] → 切换提示态时隐藏 CTA/表单双栏中的表单位或整段替换为既有 prompt，行为与现 `v-if` 链一致
