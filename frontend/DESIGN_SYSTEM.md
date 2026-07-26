# Doodle Craft 设计系统

> 极简几何 · 粗线涂鸦 · 彩绘卡通 · 手稿纸
> 令牌唯一真相源：`frontend/src/shared/styles/tokens.css`

---

## 一、视觉皮肤层 — 全局主题变量

所有视觉属性从 tokens.css 的 CSS 变量派生。本节是变量的**使用指南**，不是替代 tokens.css。

### 1.1 色板

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

### 1.2 8 模块色

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

### 1.3 状态色

| 状态 | 边框/图标 | 背景 | 文字 | 用途 |
|------|----------|------|------|------|
| 成功/在线 | `#6BCB77` | `#C8F5D0` | `#2d7a2d` | `--app-status-success` 系列 |
| 危险/失败 | `#FFB5A7` | `#FFE0DB` | `#a03030` | `--app-status-danger` 系列 |
| 紫色/锁定 | `#A78BFA` | `#E8DDF8` | `#5a3fa0` | `--app-status-purple` 系列 |
| 警告/等待 | `#F7C948` | `#FFF9E0` | `#7a5a10` | `--app-status-warning-bg` |
| 离线/禁用 | `#d4d8dc` | `#f0ede8` | `#999` | `--app-offline` |

### 1.4 字号刻度

字号最小 **12px**。所有字号使用 CSS 变量，**禁止硬编码 `font-size: Xpx`**。共 6 档：

| 刻度 | CSS 变量 | 值 | 场景 | 合并了 |
|------|------|:--:|------|:--:|
| xs | `--app-size-xs` | 12px | 按钮文字、表格列头、标签、Badge、时间戳 | 8/9/10/11 → 12 |
| sm | `--app-size-sm` | 14px | UI 正文（默认阅读字号） | 13/14/15 → 14 |
| md | `--app-size-md` | 16px | 卡片标题、表单标签、模块标题 | 16/17/18 → 16 |
| lg | `--app-size-lg` | 20px | 段落标题、弹窗标题 | 20/22 → 20 |
| xl | `--app-size-xl` | 24px | 页面标题 | 24/26/28 → 24 |
| 2xl | `--app-size-2xl` | 32px | KPI 数字、Hero 数字 | 30/32/36/40 → 32 |

**规则**：最小 12px，不允许出现刻度表之外的字号，所有 10/11px 一律用 `xs`(12px) 替代。

### 1.5 字体层级

| 层级 | 字体 | 字重 | 字号 |
|------|------|:--:|------|
| 页面标题 | `var(--app-font-display)` — Patrick Hand（英文）/ PingFang SC（中文） | 400 | `--app-size-xl` (24px) |
| 段落标题 | `var(--app-font-display)` — Patrick Hand（英文）/ PingFang SC（中文） | 400 | `--app-size-lg` (20px) |
| KPI 数字 | `var(--app-font)` — Nunito, PingFang SC | 800 | `--app-size-2xl` (32px) |
| UI 正文 | `var(--app-font)` — Nunito（英文）/ PingFang SC（中文） | 500 | `--app-size-sm` (14px) |
| 辅助文字 | `var(--app-font)` — Nunito, PingFang SC | 500 | `--app-size-xs` (12px) |
| 按钮/标签 | `var(--app-font)` — Nunito, PingFang SC | 600–700 | `--app-size-xs` (12px) |
| 代码 | `var(--app-font-mono)` — JetBrains Mono | 500–600 | `--app-size-xs` (12px) |

> Patrick Hand 仅支持 400 weight，标题不设加粗。KPI 数字用 Nunito 800 weight 而非手写体，保证数字对齐清晰。

### 1.5 圆角 — 几何不对称

| 场景 | 值 | CSS 变量 |
|------|------|------|
| 卡片 | `6px 10px 6px 10px` | `--app-radius-md` |
| 按钮 / 输入框 | `4px 8px 4px 8px` | `--app-radius-sm` |
| Badge / 标签 | `3px 6px 3px 6px` | — |
| Element Plus 组件基值 | `4px 8px` | `--el-border-radius-base` |

**禁止**：对称大圆角 `50px` `16px` `20px`。Doodle Craft 的不对称圆角是刻意设计。

### 1.6 阴影层级

| 层级 | 值 | CSS 变量 | 场景 |
|:--:|------|------|------|
| sm | `2px 2px 0 rgba(0,0,0,0.04)` | `--app-shadow-sm` | 卡片默认、纸艺卡片 |
| md | `2px 3px 0 rgba(0,0,0,0.05)` | `--app-shadow-md` | 拍立得卡片、KPI 卡 |
| lg | `3px 4px 0 rgba(0,0,0,0.06)` | `--app-shadow-lg` | 弹窗 |
| icon | `2px 2px 0 rgba(0,0,0,0.06)` | `--app-icon-shadow` | 图标装饰 |

阴影统一用扁平投影（`0` 模糊半径），不出现模糊阴影或 `rgba` 大扩散。

### 1.7 间距刻度

| 刻度 | 值 | CSS 变量 | 场景 |
|------|:--:|------|------|
| xs | 4px | `--app-space-xs` | 图标与文字紧贴间距 |
| sm | 8px | `--app-space-sm` | 标签之间、Badge 内边距 |
| md | 16px | `--app-space-md` | 卡片/面板 padding |
| lg | 24px | `--app-space-lg` | 卡片之间、表格与分页之间 |
| xl | 32px | `--app-space-xl` | 内容区 padding |
| 2xl | 48px | `--app-space-2xl` | 页面顶部/底部留白 |

**强制使用变量**，不允许出现 `padding: 15px` `gap: 20px` 等随意值。

### 1.8 动效

| 用途 | 时长 | CSS 变量 |
|------|:--:|------|
| hover 变色、图标缩放 | 0.12s | `--app-duration-fast` |
| 卡片抬起、展开/收起 | 0.15s | `--app-duration` |
| 路由切换、弹窗进出 | 0.25s | `--app-duration-slow` |

easing：普通过渡 `--app-ease: cubic-bezier(0.25,0.1,0.25,1)`，弹性动画 `--app-spring: cubic-bezier(0.34,1.56,0.64,1)`。

### 1.9 颜色使用规则

| 颜色 | 允许用途 | 禁止用途 |
|------|---------|---------|
| `--ink` | 正文、标题、图标、实色边框 | — |
| `#999` / `--app-text-secondary` | 辅助文字、占位符、禁用态 | 正文、标题 |
| `--c-*` 模块色 | 左边框装饰、图标色、图表系列色、浅色背景块 | 正文大面积使用、普通卡片背景 |
| 状态色 | Badge、状态标签、告警提示 | 正文、普通卡片背景 |
| `#FFE066` | hover 高亮背景 | 默认背景色 |

> **速查**：改颜色 → 查 §1.1 色板 / §1.3 状态色 → 用 `var(--xxx)` → 禁止字面量

---

## 二、基础 UI 原子层 — Element Plus 覆盖

所有 Element Plus 组件的 Doodle Craft 风格覆盖已在 `tokens.css` 中通过 `--el-*` 变量完成。本节是各组件状态表和使用约束。

### 2.1 Button 按钮

| 属性 | 值 |
|------|------|
| 圆角 | `4px 8px 4px 8px` |
| 边框 | `2px solid var(--ink)` |
| 字号 | 11px / 700 |
| hover | 背景 `#FFE066`，位移 `translate(1px,1px)` |
| active | 位移归零 |
| disabled | 透明度 0.5，禁止点击 |
| primary | 背景 `var(--c-dashboard)` |

**约束**：一个操作区内最多一个 primary 按钮，其余用 default。危险操作（删除、清空）用 danger 样式但放在确认弹窗中。

<details><summary>📋 可复制代码块</summary>

```css
/* 按钮 — 通用 */
:deep(.el-button) {
  font-size: 11px; font-weight: 700; padding: 6px 16px;
  border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  background: #fff; color: var(--ink);
  transition: all var(--app-duration-fast) var(--app-ease);
}
:deep(.el-button:hover) {
  background: var(--app-highlight); transform: translate(1px,1px);
}
:deep(.el-button:active) { transform: translate(0,0); }
:deep(.el-button.is-disabled) { opacity: 0.5; pointer-events: none; }

/* 按钮 — Primary（改为模块色） */
:deep(.el-button--primary) {
  background: var(--c-dashboard); color: var(--ink);
}
:deep(.el-button--primary:hover) { background: var(--app-highlight); }

/* 按钮 — Danger（放在确认弹窗中使用） */
:deep(.el-button--danger) {
  background: var(--app-status-danger); color: #fff; border-color: var(--app-status-danger);
}
```
</details>

### 2.2 Table 表格

| 属性 | 值 |
|------|------|
| 表头背景 | `linear-gradient` 暖色渐变（`--app-bg-subtle`） |
| 行分隔 | `1px dashed var(--app-border-lighter)` |
| 斑马纹 | `nth-child(even)` 微妙底色 |
| hover 行 | 浅 teal 高亮 |
| 空状态 | 居中：图标 + "暂无数据" |
| 加载态 | `v-loading` + 骨架行 |
| 边框 | 无外框，内部虚线分隔 |

**约束**：表格只能放在页面主内容区或 Tab 面板内。不能嵌在卡片中。表格需设 `max-height` + 表头固定。

<details><summary>📋 可复制代码块</summary>

```css
/* 表格 — 直接复制 */
:deep(.el-table) {
  --el-table-border-color: transparent;
  background: transparent;
}
:deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, var(--app-bg-subtle) 0%, rgba(248,246,242,0.4) 100%);
  color: var(--ink); font-weight: 700; font-size: var(--app-font-size-sm);
  border-bottom: 1px dashed var(--app-border-lighter);
}
:deep(.el-table td.el-table__cell) {
  border-bottom: 1px dashed var(--app-border-lighter);
  color: var(--ink);
}
:deep(.el-table tr:nth-child(even) td) { background: rgba(248,246,242,0.4); }
:deep(.el-table tr:hover td) { background: rgba(25,200,185,0.05); }
:deep(.el-table__empty-text) { color: var(--app-text-secondary); }
```
</details>

### 2.3 Dialog / Modal 弹窗

| 属性 | 值 |
|------|------|
| 宽度档位 | sm 420px / md 520px / lg 720px |
| 标题区 | 左对齐，`Caveat` 20px，下划线分隔 |
| 内容区 | padding `--app-space-md`，无内部滚动（内容多时让页面滚动） |
| 底部按钮 | 右对齐，取消在左 / 确认在右 |
| 遮罩 | `rgba(0,0,0,0.3)`，无模糊 |

**约束**：弹窗内不放表格。弹窗内表单宽度不超过 520px。

<details><summary>📋 可复制代码块</summary>

```css
/* 弹窗 — 直接复制，改 width 即可 */
:deep(.el-dialog) {
  border-radius: var(--app-radius-md); background: #fff;
  padding: 0; box-shadow: var(--app-shadow-lg);
}
:deep(.el-dialog__header) {
  padding: var(--app-space-md) var(--app-space-lg) var(--app-space-sm);
  border-bottom: 1px dashed var(--app-border-light);
}
:deep(.el-dialog__title) {
  font-family: var(--app-font-display); font-size: 20px; font-weight: 700; color: var(--ink);
}
:deep(.el-dialog__body) { padding: var(--app-space-md) var(--app-space-lg); }
:deep(.el-dialog__footer) {
  padding: var(--app-space-sm) var(--app-space-lg) var(--app-space-md);
  text-align: right;
  display: flex; justify-content: flex-end; gap: var(--app-space-sm);
}
:deep(.el-overlay) { background: rgba(0,0,0,0.3); }
```
</details>

### 2.4 Form / Input 表单与输入

| 属性 | 值 |
|------|------|
| label 对齐 | 左对齐，宽度 80 / 100 / 120px 三档 |
| 输入框高度 | sm 32px / md 40px / lg 48px |
| 输入框圆角 | `4px 8px 4px 8px` |
| 输入框边框 | `2px solid var(--ink)`，focus 变 `#FFE066` |
| placeholder | `#999`，字重 400 |
| 校验错误 | 边框变 `#FFB5A7`，错误文字在输入框下方 |
| 操作按钮 | 表单底部右对齐 |

**约束**：表单不放在卡片网格中。弹窗内表单只需一列，不分多列。错误提示不动布局。

<details><summary>📋 可复制代码块</summary>

```css
/* 输入框 — 直接复制 */
:deep(.el-input__wrapper) {
  border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  background: #fff; box-shadow: none; padding: 0 12px;
}
:deep(.el-input__wrapper:hover) { border-color: var(--ink); }
:deep(.el-input__wrapper.is-focus) {
  border-color: var(--app-highlight);
  box-shadow: 0 0 0 1px var(--app-highlight);
}
:deep(.el-input__inner) {
  font-family: var(--app-font); font-size: var(--app-font-size-sm);
  color: var(--ink); font-weight: 500;
}
:deep(.el-input__inner::placeholder) { color: var(--app-text-secondary); font-weight: 400; }

/* 输入框 — 错误态 */
:deep(.el-input.is-error .el-input__wrapper) { border-color: var(--app-status-danger); }
:deep(.el-form-item__error) { color: var(--app-status-danger-text); font-size: 12px; padding-top: 4px; }

/* 表单 — 标签 */
:deep(.el-form-item__label) {
  color: var(--ink); font-weight: 600; font-size: var(--app-font-size-sm);
  text-align: left; justify-content: flex-start;
}

/* 表单 — 底部按钮栏 */
.form-actions { display: flex; justify-content: flex-end; gap: var(--app-space-sm); padding-top: var(--app-space-md); }
```
</details>

### 2.5 Tag / Badge 标签

| 场景 | 背景 | 文字 | 边框 |
|------|------|------|------|
| 成功/在线 | `#C8F5D0` | `#2d7a2d` | `1.5px solid var(--ink)` |
| 失败/离线 | `#FFE0DB` | `#a03030` | `1.5px solid var(--ink)` |
| 锁定/排队 | `#E8DDF8` | `#5a3fa0` | `1.5px solid var(--ink)` |
| 警告/等待 | `#FFF9E0` | `#7a5a10` | `1.5px solid var(--ink)` |
| 禁用/未知 | `#f0ede8` | `#999` | `1.5px solid var(--ink)` |

字体 10px / 700，圆角 `3px 6px 3px 6px`。

<details><summary>📋 可复制代码块</summary>

```css
/* Badge — 选一个状态色复制，改模块名前缀 */
.module-badge {
  font-size: 10px; font-weight: 700; padding: 2px 7px;
  border: 1.5px solid var(--ink); border-radius: 3px 6px 3px 6px;
}
.badge--online  { background: var(--app-status-success-bg); color: var(--app-status-success-text); }
.badge--offline { background: #f0ede8; color: var(--app-text-secondary); }
.badge--busy    { background: var(--app-status-purple-bg); color: var(--app-status-purple-text); }
.badge--error   { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); }
.badge--warning { background: var(--app-status-warning-bg); color: #7a5a10; }
```
</details>

### 2.6 其他原子组件

| 组件 | 关键约束 |
|------|---------|
| **Pagination** | 右对齐，放在表格下方。简化版（只显示页码+箭头），不显示总数下拉 |
| **Tabs** | 激活项下划线 `2px solid var(--ink)`，内容区 padding top `--app-space-md` |
| **Select** | 下拉选项 hover `#FFE066`，选中项加粗 |
| **Cascader** | ⚠️ `emitPath` 默认 `true`，必须显式设 `emitPath: false` |
| **el-menu** | 侧边栏专用，激活项背景 `var(--c-dashboard)` |

> **速查**：改基础组件 → 查 §2 对应组件状态表 → 用 `:deep()` + `--el-*` 覆盖 → 不封装薄 wrapper

---

## 三、组件层 — 边框 + 背景 + 文字模板

组件层是模块自己的业务组件。每个组件有固定的三要素组合，不允许自由发挥。

### 3.1 拍立得卡片 (.card)

```
边框:  2.5px solid var(--ink)
背景:  #fff
文字:  --ink
圆角:  6px 10px 6px 10px
阴影:  2px 3px 0 rgba(0,0,0,0.05)
装饰:  ::before 图钉（9×9 径向渐变圆，居中置于顶部）
hover: rotate(0deg) scale(1.03)，阴影加深
```

**用途**：模块内容卡片、数据摘要卡片。

> **AI**：复制 §4.6 中的 `.card` CSS 块 → 改内容字段 → 完成。不要自己设计新卡片样式。

### 3.2 纸艺卡片 (.card-info)

```
边框:  2.5px solid var(--ink)
背景:  #fff
文字:  --ink
圆角:  4px 10px 6px 8px
阴影:  2px 2px 0 rgba(0,0,0,0.04)
hover: translate(1px,1px)，阴影收窄
```

**用途**：信息提示、次要面板、嵌套内层卡片。

> **AI**：比拍立得卡片更扁更轻。复制 `.card` CSS 块 → 去掉图钉伪元素 → 改阴影为 `--app-shadow-sm` → 完成。

### 3.3 KPI 统计卡 (.kpi-card)

```
边框:  3px solid var(--ink)
背景:  #fff
文字:  Caveat 30px / 700 (数字) + Quicksand 13px (标签)
圆角:  4px 10px 6px 8px
阴影:  2px 3px 0 rgba(0,0,0,0.04)
装饰:  顶部菱形色块（10×10，旋转45°，border: 2px solid var(--ink)）
      底部 "~" 水印（Caveat 17px，opacity 0.12）
```

**用途**：仪表盘统计数字，操作区摘要条。

> **AI**：复制 §4.6 中的 `.kpi-card` CSS 块 → 改 `kpi-dot` 的背景色为模块色 → 完成。

### 3.4 状态 Badge (.badge)

```
边框:  1.5px solid var(--ink)
背景:  状态对应背景色（见 §1.3）
文字:  状态对应文字色（见 §1.3），10px / 700
圆角:  3px 6px 3px 6px
```

### 3.5 筛选标签 (.filter-tab)

```
default:  背景 transparent，文字 #999，边框 2px solid transparent
hover:    文字 --ink
active:   背景 #fff，文字 --ink，边框 2px solid var(--ink)
圆角:     4px 8px 4px 8px
字号:     11px / 700
```

> **AI**：复制 §4.6 中的 `.filter-tab` CSS 块 → 改标签文字 → 完成。

### 3.6 操作栏

```
边框:   无
背景:   transparent
布局:   flex，左操作组 + 右操作组（space-between）
间距:   元素间 gap: --app-space-sm
```

操作按钮：字号 11px / 700，默认用 default 样式，主操作一个 primary。

> **AI**：复制 §4.6 中的 `.action-bar` CSS 块 → 改按钮数量和文字 → 完成。

### 3.7 状态模板

**空状态（列表/表格无数据时）**：
```
布局:   居中 (text-align: center)，padding: 60px 20px
图标:   模块色，opacity 0.5，64×64
文字:   #999，14px，"暂无数据"
按钮:   可选，放在文字下方 gap 12px
```

**加载骨架屏（数据请求中）**：
```
列表页:  el-skeleton + 5 行动画行
详情页:  el-skeleton + 标题/段落/图片占位
禁止:   全屏 spinner
```

**错误状态（请求失败时）**：
```
布局:   居中，padding: 40px 20px
图标:   #FFB5A7
文字:   #a03030，14px，错误信息摘要
按钮:   "重试" default 样式，放在文字下方
禁止:   白屏或无反馈
```

> **AI**：空状态 / 加载 / 错误 → 选对应模板 → 替换图标和文字 → 完成。三个模板分别是 §4.6 的 `.empty-state` / `el-skeleton` / 本节的错误布局。

### 3.8 数据行

表格行和卡片之外的第三种展示模式——适合设置项、配置列表：

```
边框:   下边框 1px dashed var(--app-border-lighter)
背景:   transparent
布局:   flex，label 左对齐 120px + value 弹性宽度
hover:  背景 var(--app-bg-subtle)
```

> **AI**：适合设置项列表。复制 flex 布局 → 改 label 文字 → 完成。

> **速查**：做组件 → 查 §3 模板 → 边框+背景+文字三要素套用 → 不做独立设计

---

## 四、页面层 — 布局骨架与滚动规则

### 4.1 标准页面骨架

```
┌──────────────────────────────────────────────┐
│ AppSidebar (228px) │ WorkbenchHeader          │  z-index: 50
├────────────────────┼──────────────────────────┤
│                    │ KPI 统计条 / 操作工具栏    │  操作区
│                    ├──────────────────────────┤
│      侧边栏        │ 筛选标签 + 视图切换        │  筛选区
│                    ├──────────────────────────┤
│                    │ 主内容区                   │  唯一纵向滚动
│                    │  · 卡片网格 / 表格 / 详情  │  flex: 1 1 0
│                    │                          │  min-height: 0
│                    │                          │  overflow-y: auto
└────────────────────┴──────────────────────────┘
```

### 4.2 页面背景

```css
background: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px);
background-size: 15px 15px;
background-color: var(--paper);
```

所有页面统一点阵纸纹。不允许纯色背景。

### 4.3 卡片网格微旋转

```css
.cards > :nth-child(3n+1) { transform: rotate(-0.6deg); }
.cards > :nth-child(3n+2) { transform: rotate(0.4deg); }
.cards > :nth-child(3n+3) { transform: rotate(-0.3deg); }
.cards > :hover { transform: rotate(0deg) scale(1.03); z-index: 5; }
```

卡片区统一使用。禁止网格中的卡片全部 0deg 排排坐。

### 4.4 滚动规则

| 区域 | 滚动 | 规则 |
|------|:--:|------|
| 页面主内容区 | 纵向 | `flex: 1 1 0; min-height: 0; overflow-y: auto` |
| 表格 | 横向 | `overflow-x: auto` + 固定表头 |
| 卡片 | 禁止 | 卡片本身不设滚动，内容溢出时裁剪或外部容器滚动 |
| 弹窗内容 | 禁止 | 弹窗不设内部滚动 |

**关键**：禁止任何中间层出现 `overflow: hidden`，会导致内容被裁剪。当前翻车记录：`info-card` 残留 `overflow:hidden` + `el-tabs__content` 的 `overflow:hidden` 三层裁剪。

### 4.5 内容区 Flex 子项规则

```
.content-area {
  flex: 1 1 0;        /* 必须，让内容区占满剩余高度 */
  min-height: 0;      /* 必须，覆盖 Flexbox 默认 min-height:auto */
  overflow-y: auto;   /* 必须，唯一纵向滚动容器 */
}
```

不设这三个属性 → 内容溢出时页面无法滚动。

### 4.5.1 内容区宽度规则

**禁止在全局样式对内容区设置 `max-width` 并居中。** 各模块通过自身 scoped CSS 决定是否需要限制内容宽度。

**错误示例**（已修复的全局 bug）：
```css
/* ❌ 全局 style.css — 所有模块被 1600px 卡住，大屏两侧大量留白 */
.doc-body {
  max-width: 1600px;
  margin: 0 auto;
}
```

**正确做法**：
```css
/* ✅ 模块自身决定宽度策略 */
/* 默认：内容填满可用空间（dashboard、device-pool、element-locator 等） */
.module-page .doc-body {
  flex: 1 1 0;
  min-height: 0;
  overflow-y: auto;
  /* 不设 max-width */
}

/* 需要限制宽度时：模块自己加 */
.reading-page .doc-body {
  max-width: 900px;   /* 长文本阅读舒适宽度 */
  margin: 0 auto;
}
```

**使用场景判断**：

| 场景 | 是否需要 max-width | 理由 |
|------|:--:|------|
| 仪表盘、设备管理（卡片网格/表格/图表） | ❌ | 内容密度高、多列布局，天然需要更多横向空间 |
| 元素定位（截图 + 元素树并排） | ❌ | 左右分栏，限制宽度会压缩操作区 |
| 长文本阅读、Markdown 渲染 | ✅ | `max-width: 700-900px` 保证阅读舒适度 |
| 表单填写页 | ⚠️ 可选 | 表单过宽时光标移动距离大，建议 `max-width: 800px` |

**翻车记录**：全局 `.doc-body` 设了 `max-width: 1600px; margin: 0 auto`，导致所有模块在大屏（2560px+）下内容区卡在 1600px，两侧各有 ~480px 空白。已从 `style.css` 移除此规则，改为模块按需自定。

### 4.6 标准页面模板 — 直接复制，改内容即可

```vue
<template>
  <div class="module-page">
    <!-- 操作区：左 KPI 摘要 + 右操作按钮 -->
    <div class="action-bar">
      <div class="action-bar__left">
        <div class="kpi-row">
          <div class="kpi-card" v-for="k in kpis" :key="k.label">
            <div class="kpi-dot" :style="{ background: k.color }"></div>
            <div class="kpi-value">{{ k.value }}</div>
            <div class="kpi-label">{{ k.label }}</div>
          </div>
        </div>
      </div>
      <div class="action-bar__right">
        <button class="btn" @click="handleRefresh">刷新</button>
        <button class="btn btn-primary" @click="handleCreate">新建</button>
      </div>
    </div>

    <!-- 筛选区：标签 + 搜索 + 视图切换 -->
    <div class="filter-bar">
      <div class="filter-tabs">
        <span class="filter-tab active">全部 ({{ total }})</span>
        <span class="filter-tab">启用中 ({{ active }})</span>
        <span class="filter-tab">已归档 ({{ archived }})</span>
      </div>
      <div class="filter-actions">
        <el-input v-model="keyword" placeholder="搜索..." size="small" />
      </div>
    </div>

    <!-- 内容区：唯一纵向滚动容器 -->
    <div class="content-area">
      <!-- 空状态 -->
      <div v-if="!list.length" class="empty-state">
        <el-icon :size="64" color="var(--c-device)" style="opacity:0.5"><Folder /></el-icon>
        <p>暂无数据</p>
        <button class="btn" @click="handleCreate">新建</button>
      </div>

      <!-- 卡片网格 -->
      <div v-else class="cards">
        <div v-for="item in list" :key="item.id" class="card"
             @click="handleClick(item)">
          <div class="card__title">{{ item.name }}</div>
          <div class="card__meta">{{ item.description }}</div>
          <div class="card__footer">
            <span class="badge" :class="statusBadge(item.status)">{{ item.status }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.module-page {
  display: flex; flex-direction: column; height: 100%;
  background: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px) 0 0 / 15px 15px;
  background-color: var(--paper);
}

/* ── 操作区 ── */
.action-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 0 var(--app-space-lg) 0; gap: var(--app-space-md);
}
.action-bar__right { display: flex; gap: var(--app-space-sm); }

/* ── KPI 行 ── */
.kpi-row { display: flex; gap: var(--app-space-md); }
.kpi-card {
  text-align: center; padding: 12px 20px 16px; background: #fff;
  border: var(--app-border-width) solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-sm); position: relative;
}
.kpi-dot { width: 10px; height: 10px; transform: rotate(45deg); margin: 0 auto 5px; border: 2px solid var(--ink); }
.kpi-value { font-family: var(--app-font-display); font-size: 30px; font-weight: 700; color: var(--ink); }
.kpi-label { font-size: var(--app-font-size-sm); color: var(--app-text-secondary); margin-top: 2px; }
.kpi-card::after { content: '~'; position: absolute; bottom: 2px; right: 8px; font-family: var(--app-font-display); font-size: 17px; opacity: 0.12; }

/* ── 筛选区 ── */
.filter-bar {
  display: flex; justify-content: space-between; align-items: center;
  padding-bottom: var(--app-space-md);
}
.filter-tabs { display: flex; gap: var(--app-space-sm); }
.filter-tab {
  padding: 4px 12px; font-size: 11px; font-weight: 700; color: var(--app-text-secondary);
  background: transparent; border: 2px solid transparent;
  border-radius: var(--app-radius-sm); cursor: pointer;
  transition: color var(--app-duration-fast) var(--app-ease);
}
.filter-tab:hover { color: var(--ink); }
.filter-tab.active { color: var(--ink); background: #fff; border-color: var(--ink); }

/* ── 按钮 ── */
.btn {
  font-size: 11px; font-weight: 700; padding: 6px 16px;
  border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  background: #fff; color: var(--ink); cursor: pointer;
  transition: all var(--app-duration-fast) var(--app-ease);
}
.btn:hover { background: var(--app-highlight); transform: translate(1px,1px); }
.btn-primary { background: var(--c-dashboard); }

/* ── 内容区（关键：唯一滚动容器）── */
.content-area {
  flex: 1 1 0; min-height: 0; overflow-y: auto;
  padding: var(--app-space-md) 0;
}

/* ── 卡片网格 ── */
.cards {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--app-space-lg);
}
.cards > :nth-child(3n+1) { transform: rotate(-0.6deg); }
.cards > :nth-child(3n+2) { transform: rotate(0.4deg); }
.cards > :nth-child(3n+3) { transform: rotate(-0.3deg); }
.cards > :hover { transform: rotate(0deg) scale(1.03); z-index: 5; }

/* ── 卡片 ── */
.card {
  background: #fff; border: var(--app-border-width) solid var(--ink);
  border-radius: var(--app-radius-md); padding: var(--app-space-md) var(--app-space-md) 30px;
  box-shadow: var(--app-shadow-md); position: relative; cursor: pointer;
  transition: transform var(--app-duration) var(--app-ease);
}
.card::before {
  content: ''; position: absolute; top: 4px; left: 50%; transform: translateX(-50%);
  width: 9px; height: 9px;
  background: radial-gradient(circle, var(--app-pushpin-light) 30%, #c0b8a8 60%, var(--app-pushpin-dark) 100%);
  border-radius: 50%; box-shadow: 0 1px 1px rgba(0,0,0,0.08);
}
.card__title { font-family: var(--app-font-display); font-size: 20px; font-weight: 700; color: var(--ink); margin-bottom: 6px; }
.card__meta { font-size: var(--app-font-size-sm); color: var(--app-text-secondary); margin-bottom: 12px; }
.card__footer { display: flex; justify-content: space-between; align-items: center; }

/* ── Badge ── */
.badge {
  font-size: 10px; font-weight: 700; padding: 2px 7px;
  border: 1.5px solid var(--ink); border-radius: 3px 6px 3px 6px;
}
.badge.success { background: var(--app-status-success-bg); color: var(--app-status-success-text); }
.badge.danger  { background: var(--app-status-danger-bg);  color: var(--app-status-danger-text); }

/* ── 空状态 ── */
.empty-state {
  text-align: center; padding: 60px 20px; color: var(--app-text-secondary);
}
.empty-state p { margin: var(--app-space-md) 0; font-size: 14px; }
```

> **AI 使用说明**：新模块页面 → 复制 `<template>` 和 `<style scoped>` → 改 KPI 字段名 / 筛选标签 / 卡片字段 → 完成。不要重新设计布局。
> 如果页面用表格而非卡片 → 把 `.cards` 换成 `el-table`，保留操作区和筛选区不变。

> **速查**：改布局 → 查 §4.1 骨架 → 验 §4.4 滚动 → 上 §4.3 微旋转

---

## 五、工程约束

### 5.1 组件嵌套深度 — MAX 4 层

```
Level 1: 页面容器 (index.vue)
  Level 2: 区域 (操作区 / 筛选区 / 内容区)
    Level 3: 卡片 / 表格 / 面板
      Level 4: 内容元素 (文本/徽标/按钮/输入框) ← 最底层
```

禁止 Level 5。出现"卡片里放卡片再放卡片"就该拆组件。

### 5.2 表格放置

| 允许放 | 禁止放 |
|--------|--------|
| 页面主内容区 | 卡片内部 |
| Tab 面板 | 其他表格内部 |
| 抽屉/弹窗 body（需 max-height） | 筛选区/操作区 |

### 5.3 表单布局

| 规则 | 说明 |
|------|------|
| label 对齐 | 左对齐，固定宽度 80/100/120px |
| 操作按钮 | 表单底部右对齐，取消左/确认右 |
| 弹窗内表单 | 单列，弹窗宽度 ≤ 520px |
| 错误提示 | 输入框下方，不动布局 |

### 5.4 空/加载/错误三态

| 状态 | 模板 | 禁止 |
|------|------|------|
| 无数据 | 居中：图标 + "暂无数据" | 空白列表 |
| 加载中 | 骨架屏 / el-skeleton | 全屏 spinner |
| 请求失败 | 错误信息 + "重试"按钮 | 白屏 |

每个列表/表格组件必须有这三个状态的处理。

### 5.5 z-index 层级

```
90: 侧边栏
80: 抽屉 (el-drawer)
70: 弹窗 (el-dialog) + 遮罩
60: 下拉菜单 / Select 弹出层
50: 固定头部 (WorkbenchHeader)
 0: 内容区
```

### 5.6 图标

- 统一用 Element Plus Icon
- 尺寸三档：14px / 16px / 20px
- 颜色跟随父元素文字色（`currentColor`）
- 不混用 emoji / 自定义 SVG / 图片图标

### 5.7 动画范围

| 允许动画 | 禁止动画 |
|---------|---------|
| hover 变色 / 图标缩放 | 表单输入时的布局抖动 |
| 卡片抬起 / 下压 | 数据更新时的过渡动画 |
| 展开 / 收起 | 页面初始化加载动画 |
| 路由切换 | 表格排序/筛选动画 |

### 5.8 文件组织

```
模块 scoped CSS     → 放 .vue 的 <style scoped> 块
跨模块共享样式       → 放 tokens.css（通过 --app-* 变量）
全局覆盖 Element Plus → 放 tokens.css（通过 --el-* 变量）
禁止                → 在 style.css 全局写模块专属样式
```

### 5.9 CSS 变量安全边界

| 上下文 | CSS 变量 `var(--*)` | 必须用字面量 |
|--------|:--:|:--:|
| `<style>` / `.css` | ✅ | |
| 内联 `:style=""` | ✅ | |
| **ECharts 配置** | | ❌ `#xxx` |
| **Canvas API** | | ❌ `#xxx` |
| **SVG 动态生成** | | ❌ `#xxx` |

Canvas 渲染引擎不解析 CSS 变量。改 tokens.css 后需同步更新 JS 渲染配置。

### 5.10 响应式

| 断点 | 行为 |
|------|------|
| > 768px | 正常桌面布局 |
| ≤ 768px | 侧边栏折叠，卡片网格 2→1 列 |

移动端不强制 PWA 适配（平台以桌面使用为主）。

### 5.11 禁止事项

- ❌ `backdrop-filter: blur()` — 全局清零
- ❌ `var(--app-glass-*)` — 已设为透明/白底
- ❌ 对称大圆角 `50px` `16px` `20px`
- ❌ 旧 Soft Glass 色值 `#4a4e69` `#9a8c98`
- ❌ 新模块引入玻璃态样式
- ❌ 在 `style.css` 全局写模块专属样式
- ❌ 组件 scoped 中硬编码色值（必须走 `var(--*)`）
- ❌ 硬编码 `font-size: Xpx`（必须走 `--app-size-*` 刻度变量）

---

## 速查索引

| 你要做什么 | 查哪节 |
|-----------|--------|
| 改颜色 / 加颜色 | §1.1 色板 + §1.3 状态色 + §1.9 颜色使用规则 |
| 改字体 / 字号 | §1.4 字体层级 |
| 改间距 / padding | §1.7 间距刻度（用变量，不写字面量） |
| 改圆角 | §1.5 圆角（不对称规则） |
| 改阴影 | §1.6 阴影层级 |
| 改动效 / 加动画 | §1.8 动效 + §5.7 动画范围 |
| 改按钮 / 表格 / 弹窗 / 表单 / 输入框 | §2 基础 UI 原子层 |
| 做新卡片 / Badge / 筛选标签 / KPI 卡 | §3 组件层模板 |
| 做空状态 / 加载 / 错误提示 | §3.7 状态模板 |
| 改页面布局 | §4 页面层 + §5.1 嵌套深度 |
| 放表格 | §5.2 表格放置规则 |
| 放弹窗 | §2.3 Dialog + §5.5 z-index |
| 做表单 | §2.4 Form + §5.3 表单布局规则 |
| 调 z-index | §5.5 z-index 层级 |
| 用图标 | §5.6 图标 |
| 放图表（ECharts/Canvas） | §5.9 CSS 变量安全边界 |
| 排查页面不可滚动 | §4.4 滚动规则 |
| 新模块做样式 | §5.8 文件组织 + §5.11 禁止事项 |
