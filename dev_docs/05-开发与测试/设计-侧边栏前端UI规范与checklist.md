# 侧边栏前端 UI 规范与 Checklist

> 版本 v1 · 2026-08-14
> 适用范围：`frontend/src/shared/components/AppSidebar.vue` 及配套（sidebarNavConfig.ts / useSidebarResize.ts）
> 设计语言：Doodle Craft（手稿纸 · 粗线涂鸦 · 彩绘卡通），与主功能区同源
> 唯一真相源：`frontend/src/shared/styles/tokens.css`（令牌）、`frontend/DESIGN_SYSTEM.md`（设计系统）

---

## 1. 组件归属

| 项 | 说明 |
|----|------|
| 组件位置 | `frontend/src/shared/components/AppSidebar.vue`（shared 共享层，**不属于任何业务模块**） |
| 挂载点 | `frontend/src/App.vue` —— 所有登录后页面共用 |
| 导航配置 | `sidebarNavConfig.ts`（8 个模块菜单项登记处，增删菜单改这里） |
| 交互逻辑 | `useSidebarResize.ts`（宽度拖拽/折叠）、`animations`（入场动效） |

---

## 2. 字体规范

### 2.1 字体系列（侧边栏只允许 2 种字体）

| 字体 | CSS 变量 | 用途 | 字重限制 |
|------|----------|------|---------|
| 字库星球飞扬体 Ziku FeiYang | `--app-font-brand` | 品牌区（AI / 自动化测试平台） | **仅 400**，禁加粗（只有 Regular 字重） |
| Cascadia Mono + 思源黑体 | `--app-font` | 其余全部元素（导航项/用户区/按钮/菜单） | 400–800 |

> 全局字体架构：英文 Cascadia Mono（本机零下载 / jsDelivr woff2 兜底），中文思源黑体 Noto Sans SC（Google Fonts 分片），品牌飞扬体为本地子集 1.4MB（仅含平台字符）。
> ⚠️ 原生 `<button>` 不继承父级 font-family，**必须显式声明**（历史 bug：折叠按钮曾渲染为 Arial）。

### 2.2 字号层级（最小 14px，当前 5 档）

| 字号 | 写法 | 元素 |
|------|------|------|
| 32px | `var(--app-size-2xl)` ✅ | 品牌 "AI" |
| 30px | 字面量（用户指定值，不在 6 档刻度） | 品牌 "自动化测试平台" |
| 18px | 字面量（用户指定值） | 导航项 / 导航标签 |
| 16px | `var(--app-size-md)` ✅ | 底部用户区全部（标签/显示名/箭头/状态/退出/折叠/账号菜单） |
| 14px | `var(--app-size-sm)` ✅ | 导航 Badge、active 微光 ✦ |

### 2.3 字重规则

| 元素 | 字重 |
|------|------|
| 品牌区（飞扬体） | 400（**禁设加粗**，会触发合成伪粗） |
| 导航项（未选中） | 500 |
| 导航项（选中） | 700 |
| 用户显示名 / 标签 / 退出按钮 / 账号菜单项 | 700 |
| 用户状态 / 添加账号 | 600 |
| 折叠按钮 | 800 |

---

## 3. 颜色规范

### 3.1 必须使用 token，禁止硬编码色值

| 用途 | Token | 值 |
|------|-------|-----|
| 描边 / 文字（主） | `var(--ink)` | #1e1e24 |
| 未激活导航文字 | `var(--app-nav-text)` | #5a5547 暖灰 |
| 辅助文字 / 未激活图标 | `var(--app-ink-muted)` | #999 |
| hover 荧光黄 | `var(--app-highlight)` | #FFE066 |
| 纸底 | `var(--paper)` | #fefcf5 |
| 白纸卡底 | `#fff` 字面量（沿用既有惯例） | — |
| 分割线（header 底边 / 账号菜单分隔线） | `var(--dot)` | #d8d2c4 暖纸点色 |
| 容器投影 | `var(--app-shadow-sm)` | 2px 2px 0 rgba(0,0,0,0.04) |
| ink 半透明薄纱（拖拽条 hover） | `color-mix(in srgb, var(--ink) 4%, transparent)` | ink 4% |
| 退出按钮填充 | `var(--c-workflow)` | #89CFF0 天蓝 |
| 在线状态文字 | `var(--app-status-success-text)` | #2d7a2d |
| Badge 紫底 / 紫字 | `#E8DDF8` / `#5a3fa0` 字面量（状态紫系列，与 tokens 1.3 状态色表一致） | — |
| Badge"待开发"黄 | `#fefcbf` / `#975a16` 字面量（既有状态色） | — |

> ⚠️ `--app-border-light`（#e8ecf1）值属冷灰蓝系（§4 禁止项），**侧边栏禁止引用**——曾用于 header 底边与菜单分隔线，已改 `var(--dot)`。同理 `--app-bg-subtle` 等冷灰系 token 也不得在侧边栏使用。

### 3.2 模块色书签映射（active 左侧书签条）

路径 → 模块色映射定义在 `sidebarNavConfig.ts` 的 `MOD_COLORS` 常量：

| 路径 | 模块色 |
|------|--------|
| /dashboard | `--c-dashboard` #F7C948 柠黄 |
| /devices、/inspector | `--c-device` #6BCB77 薄荷绿 |
| /elements | `--c-element` #A78BFA 薰衣草紫 |
| /cases | `--c-case` #4ECDC4 青绿 |
| /runner | `--c-runner` #FFB5A7 桃粉 |
| /reports | `--c-report` #7C6F83 灰紫 |
| /ai-assistant、/digital-human | `--c-ai` #E879F9 柔粉紫 |
| /workflow | `--c-workflow` #89CFF0 天蓝 |

> 新增导航项时：① 在 `sidebarNavConfig.ts` 登记 ② 在 `MOD_COLORS` 补映射，缺省回落 `var(--c-workflow)`。

---

## 4. 风格语言（Doodle Craft 交互态）

| 风格元素 | 规格 | 应用处 |
|---------|------|--------|
| 墨色描边 | 2px solid `var(--ink)`（外壳右边框 3px） | 卡片/按钮/active 项/菜单 |
| 不对称圆角 | `var(--app-radius-sm)` 4px 8px（Badge 3px 6px） | 全部控件，**禁止对称大圆角** |
| 扁平投影 | `var(--app-shadow-sm/md/lg)`（0 模糊半径） | 按钮/用户卡/账号菜单 |
| 荧光笔 hover | 背景 `var(--app-highlight)` + 墨色文字 + 右移 2px | 导航项/按钮/菜单项 |
| 模块色书签 | active 左侧 5px 色条 + 2px ink 边 | active 导航项 |
| 折角 clip-path | 右上 12px 斜切角 | active 导航项 |
| 微光 ✦ | 右端闪烁（dc-twinkle 2.4s） | active 导航项 |
| 状态 Badge | 1.5px ink 边 + 不对称圆角 + 状态色底 | 导航 Badge |
| 禁止项 | ❌ 冷灰蓝系（#718096/#a0aec0/#f7fafc/#1a202c/#e8ecf1/#d4d8dc）❌ 对称大圆角 ❌ 模糊阴影 | — |

---

## 5. 布局规格（底部用户区）

| 元素 | 规格 |
|------|------|
| 用户卡 | 2px ink 边 + `--app-radius-sm` + `--app-shadow-sm`，margin 10px |
| 用户行（在线 + 退出） | `.sidebar__user-row` flex，`justify-content: space-between` —— 在线**左对齐**、退出**右对齐**，同行垂直居中 |
| 退出按钮 | 天蓝填充 `--c-workflow` + ink 描边 + 不对称圆角；hover 荧光黄；16px/700 |
| 折叠按钮 / 折叠态退出 ⎋ | 原生 button，**显式 `font-family: var(--app-font)`** |
| 账号菜单 | 用户卡上方弹出（bottom:100%），2px ink 边 + `--app-shadow-lg` 扁平投影 |

---

## 6. 前端 Checklist（改侧边栏必查）

### 6.1 字体

- [ ] 全侧边栏字体族只有 2 种：Ziku FeiYang（品牌）/ Cascadia Mono+Noto Sans SC（其余）
- [ ] 飞扬体元素字重 = 400，无 700/800
- [ ] 无元素字号 < 14px
- [ ] 32px 用 `--app-size-2xl`、16px 用 `--app-size-md`、14px 用 `--app-size-sm`，不写字面量
- [ ] 30/18px 为约定字号（字面量，用户指定值），不随手改动
- [ ] 原生 button（toggle/icon-logout）有显式 `font-family`，浏览器实测非 Arial

### 6.2 颜色

- [ ] 无硬编码色值（grep `#[0-9a-fA-F]{3,8}` 除白名单：#fff、#E8DDF8、#5a3fa0、#fefcbf、#975a16）
- [ ] 无硬编码 rgba（grep `rgba(` 应为零命中；投影走 `--app-shadow-*`，ink 半透明走 color-mix）
- [ ] 不引用 `--app-border-light`（grep `--app-border-light`，其值 #e8ecf1 属冷灰蓝系）
- [ ] 冷灰蓝系零残留（grep `#718096|#a0aec0|#f7fafc|#1a202c|#e8ecf1|#d4d8dc`）
- [ ] 新增导航项已登记 `MOD_COLORS` 映射
- [ ] 状态色走 token（在线绿 = `--app-status-success-text`）

### 6.3 风格

- [ ] 所有控件墨色描边 2px + 不对称圆角 + 扁平投影（无模糊阴影）
- [ ] hover 态为荧光黄 `--app-highlight`，无冷白/藏青
- [ ] active 态 = 白纸卡 + 2px ink 边 + 折角 + 模块色书签条 + ✦
- [ ] 新增/改动交互态与主功能区（仪表盘卡片等）同语言

### 6.4 布局与交互

- [ ] "在线"左对齐、"退出"右对齐，同行垂直居中（`.sidebar__user-row`）
- [ ] `data-testid` 保持：`sidebar-logout`、`sidebar-active-account`、`sidebar-account-menu` 等
- [ ] 交互元素键盘可达：导航（品牌/菜单项/添加账号）为 `router-link`，分组标题/用户显示/账号项为原生 `button`（全组件无 div @click；开关类带 `aria-expanded`）
- [ ] 折叠态（64px）渲染正常：⎋ 退出图标、`sidebar__toggle` 居中
- [ ] 折叠/展开切换、账号菜单弹出、拖拽调宽均正常
- [ ] 布局裁剪：窗口缩小时侧边栏导航区可滚，不挤压主区

### 6.5 验证方式

- [ ] 浏览器实测（非仅看代码）：DevTools computed style 抽查字号/字体/颜色
- [ ] 全侧边栏扫描脚本确认字号 ≥14px、字体族仅 2 种
- [ ] 检查测试未依赖被改样式（`grep -rn "sidebar-menu\|sidebar__" frontend/tests/`）

---

## 7. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-14 | 侧边栏内部交互态由冷灰蓝 SaaS 语言重绘为 Doodle Craft（荧光笔 hover/模块色书签/纸胶带分组/ink 控件） |
| 2026-08-14 | 字号层级调整：品牌 30px、胶带 22px（飞扬体）、导航项 18px、底部用户区统一 16px，最小字号定为 14px |
| 2026-08-14 | 字体收敛：全侧边栏字体族仅 Ziku FeiYang + Cascadia Mono；修复原生 button 不继承字体（Arial bug） |
| 2026-08-14 | 颜色/字号 token 收敛：在线绿 → `--app-status-success-text`；32/16/14px 字号 → token |
| 2026-08-14 | 退出按钮改天蓝填充，与"在线"同行（左对齐/右对齐） |
| 2026-08-14 | 终审加固：`--app-border-light`（冷灰蓝）→ `var(--dot)`；账号菜单项 600→700（添加账号保持 600）；容器投影 → `--app-shadow-sm`、拖拽条薄纱 → color-mix；清理 header 死代码 font-weight |
| 2026-08-14 | A11y 加固：6 处 div @click → `router-link` / 原生 `button`（键盘可达 + 语义 + aria-expanded）；导航区 `min-height:0`、用户区 `flex-shrink:0`（矮窗口防裁剪） |
| 2026-08-14 | 移除分组标题胶带（"测试全流程"/"AI 与编排"）与分组折叠机制——导航改为扁平列表；同步清理 expandedSections/GROUP_TAPE_BG/胶带样式 |
