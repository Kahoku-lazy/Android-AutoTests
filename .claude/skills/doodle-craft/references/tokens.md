# Doodle Craft 视觉皮肤层 — 全局主题变量使用指南

> 来源：`frontend/DESIGN_SYSTEM.md` §一。令牌值唯一真相源：`frontend/src/shared/styles/tokens.css`。
> 令牌值以 tokens.css 为准；改令牌时同步更新本文件与 tokens.css。

## 1.1 色板

| CSS 变量 | 色值 | 用途 |
|----------|------|------|
| `--ink` | `#1e1e24` | 正文标题、图标、实色边框 |
| `--paper` | `#fefcf5` | 页面背景 |
| `--dot` | `#d8d2c4` | 点阵纸纹圆点 |
| `--app-bg-subtle` | `#f8f6f2` | 表头、卡片微妙底色 |
| `--app-border-light` | `#e8ecf1` | 内部浅分割线 |
| `--app-border-lighter` | `#f0ede8` | 表格行线 |
| `--app-highlight` | `#FFE066` | hover 高亮背景 |
| `--app-text-secondary` | `#999` | 辅助文字、占位符、禁用态 |
| `--app-nav-text` | `#5a5547` | 侧边栏导航未激活文字（暖灰，纸面语言） |

## 1.2 8 模块色

| 模块 | CSS 变量 | 色值 |
|------|----------|------|
| dashboard | `--c-dashboard` | `#F7C948` |
| device-pool | `--c-device` | `#6BCB77` |
| element-locator | `--c-element` | `#A78BFA` |
| case-manager | `--c-case` | `#4ECDC4` |
| test-runner | `--c-runner` | `#FFB5A7` |
| report-generator | `--c-report` | `#7C6F83` |
| ai-assistant | `--c-ai` | `#E879F9` |
| workflow | `--c-workflow` | `#89CFF0` |

## 1.3 状态色

| 状态 | 边框/图标 | 背景 | 文字 | 用途 |
|------|----------|------|------|------|
| 成功/在线 | `#6BCB77` | `#C8F5D0` | `#2d7a2d` | `--app-status-success` 系列 |
| 危险/失败 | `#FFB5A7` | `#FFE0DB` | `#a03030` | `--app-status-danger` 系列 |
| 紫色/锁定 | `#A78BFA` | `#E8DDF8` | `#5a3fa0` | `--app-status-purple` 系列 |
| 警告/等待 | `#F7C948` | `#FFF9E0` | `#7a5a10` | `--app-status-warning-bg` |
| 离线/禁用 | `#d4d8dc` | `#f0ede8` | `#999` | `--app-offline` |

## 1.4 字号刻度

字号最小 12px，只允许 6 档，**禁止硬编码 `font-size`**。

| 刻度 | CSS 变量 | 值 | 场景 |
|------|------|:--:|------|
| xs | `--app-size-xs` | 12px | 按钮文字、表格列头、标签、Badge、时间戳 |
| sm | `--app-size-sm` | 14px | UI 正文（默认阅读字号） |
| md | `--app-size-md` | 16px | 卡片标题、表单标签、模块标题 |
| lg | `--app-size-lg` | 20px | 段落标题、弹窗标题 |
| xl | `--app-size-xl` | 24px | 页面标题 |
| 2xl | `--app-size-2xl` | 32px | KPI 数字、Hero 数字 |

## 1.5 字体层级

| 层级 | 字体 | 字重 | 字号 |
|------|------|:--:|------|
| 页面标题 | `--app-font-display` Cascadia Mono / Noto Sans SC | 400–700 | `--app-size-xl` 24px |
| 段落标题 | `--app-font-display` | 400–700 | `--app-size-lg` 20px |
| 品牌文字 | `--app-font-brand` Ziku FeiYang（字库星球飞扬体）| 400 | 22–32px（登录页 Hero / 侧边栏品牌）|
| KPI 数字 | `--app-font` Cascadia Mono / Noto Sans SC | 800 | `--app-size-2xl` 32px |
| UI 正文 | `--app-font` Cascadia Mono / Noto Sans SC | 500 | `--app-size-sm` 14px |
| 辅助文字 | `--app-font` | 500 | `--app-size-xs` 12px |
| 按钮/标签 | `--app-font` | 600–700 | `--app-size-xs` 12px |
| 代码 | `--app-font-mono` Cascadia Mono | 400–700 | `--app-size-xs` 12px |

> 全局字体：英文 Cascadia Mono（等宽，本机已装零下载，否则 jsDelivr woff2），中文思源黑体 Noto Sans SC（Google Fonts 分片加载）。品牌文字例外用 Ziku FeiYang（本地文件 `/fonts/ziku-feiyang.ttf`，已子集化 1.4MB，仅 Regular 字重）。Blockly 等 JS 画布渲染不解析 CSS 变量，字体用字面量——改全局字体时需同步 `TestCaseBlockly.vue` 的 `fontStyle.family`。

## 1.6 圆角 — 几何不对称

| 场景 | 值 | CSS 变量 |
|------|------|------|
| 卡片 | `6px 10px 6px 10px` | `--app-radius-md` |
| 按钮 / 输入框 | `4px 8px 4px 8px` | `--app-radius-sm` |
| Badge / 标签 | `3px 6px 3px 6px` | — |
| Element Plus 基值 | `4px 8px` | `--el-border-radius-base` |

**禁止**：对称大圆角 `50px` `16px` `20px`。

## 1.7 阴影层级

| 层级 | 值 | CSS 变量 | 场景 |
|:--:|------|------|------|
| sm | `2px 2px 0 rgba(0,0,0,0.04)` | `--app-shadow-sm` | 卡片默认、纸艺卡片 |
| md | `2px 3px 0 rgba(0,0,0,0.05)` | `--app-shadow-md` | 拍立得卡片、KPI 卡 |
| lg | `3px 4px 0 rgba(0,0,0,0.06)` | `--app-shadow-lg` | 弹窗 |
| icon | `2px 2px 0 rgba(0,0,0,0.06)` | `--app-icon-shadow` | 图标装饰 |

阴影统一扁平投影（0 模糊半径），禁止模糊阴影或大扩散。

## 1.8 间距刻度

| 刻度 | 值 | CSS 变量 | 场景 |
|------|:--:|------|------|
| xs | 4px | `--app-space-xs` | 图标与文字紧贴 |
| sm | 8px | `--app-space-sm` | 标签之间、Badge 内边距 |
| md | 16px | `--app-space-md` | 卡片/面板 padding |
| lg | 24px | `--app-space-lg` | 卡片之间、表格与分页之间 |
| xl | 32px | `--app-space-xl` | 内容区 padding |
| 2xl | 48px | `--app-space-2xl` | 页面顶部/底部留白 |

**强制用变量**，禁止 `padding: 15px` `gap: 20px` 随意值。

## 1.9 动效

| 用途 | 时长 | CSS 变量 |
|------|:--:|------|
| hover 变色、图标缩放 | 0.12s | `--app-duration-fast` |
| 卡片抬起、展开/收起 | 0.15s | `--app-duration` |
| 路由切换、弹窗进出 | 0.25s | `--app-duration-slow` |

easing：`--app-ease: cubic-bezier(0.25,0.1,0.25,1)`、`--app-spring: cubic-bezier(0.34,1.56,0.64,1)`。

## 1.10 颜色使用规则

| 颜色 | 允许用途 | 禁止用途 |
|------|---------|---------|
| `--ink` | 正文、标题、图标、实色边框 | — |
| `#999` / `--app-text-secondary` | 辅助文字、占位符、禁用态 | 正文、标题 |
| `--c-*` 模块色 | 左边框装饰、图标色、图表系列色、浅色背景块 | 正文大面积、普通卡片背景 |
| 状态色 | Badge、状态标签、告警提示 | 正文、普通卡片背景 |
| `#FFE066` | hover 高亮背景 | 默认背景色 |

> 速查：改颜色 → 查 1.1 色板 / 1.3 状态色 → 用 `var(--xxx)` → 禁止字面量。

## 1.11 仪表盘统计卡（奶油低饱和 · 参考图配色）

| CSS 变量 | 色值 | 用途 |
|----------|------|------|
| `--app-stat-line` | `#7a7874` | 卡片软灰线条（描边/十字收角/图标） |
| `--app-stat-line-soft` | `#9e9994` | 辅助文字 |
| `--app-stat-text` | `#5f5d59` | 卡片主文字 |
| `--app-stat-hover` | `#f5eecf` | hover 奶油黄 |
| `--app-stat-shadow` / `-hover` | `rgba(122,120,116,.14)` / `.22` | 扁平投影 |
| `--app-stat-sage` | `#e6f0ea` | 薄荷淡绿填充 |
| `--app-stat-gray` | `#dedfdc` | 柔灰填充 |
| `--app-stat-rose` | `#f4e8e1` | 浅粉填充 |
| `--app-stat-pale` | `#f0f6e7` | 淡青柠奶油填充 |
| `--app-stat-deep` | `#cdd9d3` | 深一档薄荷填充 |
| `--app-stat-cream` | `#fdf7ed` | 米白填充 |
| `--app-stat-dust` | `#d0c5c1` | 灰粉填充 |
