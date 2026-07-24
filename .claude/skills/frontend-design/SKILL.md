---
name: frontend-design
description: Doodle Craft 主题前端 UI 开发。新页面/新组件/改样式时使用——提供主题令牌、组件模板、页面骨架、可复制 CSS 代码块。触发：做页面、做组件、改 UI、改样式、新模块。
---

# 前端 UI 开发 — Doodle Craft

> 你是一个熟悉 Doodle Craft 设计系统的 Vue 3 前端工程师。
> 设计令牌 → `frontend/DESIGN_SYSTEM.md` | 编码工作流 → `frontend/CLAUDE.md`

## 核心原则

1. **复制，不发明**：每个 UI 元素都有预定义的模板和代码块。复制最接近的模板，改内容字段。不要从零设计。
2. **令牌，不硬编码**：所有颜色/间距/圆角/阴影用 `var(--xxx)`，不写字面量。例外：ECharts/Canvas JS 配置必须用字面量。
3. **四层，不越界**：页面骨架 → 基础原子(Element Plus) → 业务组件(卡片/Badge/KPI) → 视觉令牌(tokens.css)。上层不反向侵入下层。

---

## 开始之前：判定你在做什么

```
用户指令 →
  ├── "新建一个页面" / "做XX模块"        → 用 §页面模板
  ├── "加一个卡片" / "做数据展示"         → 用 §组件模板
  ├── "改按钮/表格/弹窗/表单/输入框样式"   → 用 §基础原子
  ├── "改颜色/字体/间距/圆角"             → 用 §视觉皮肤
  ├── "加个筛选区/操作栏/空状态"          → 用 §页面模板中的对应区域
  └── 不确定                              → 先 Glob 模块 → Read index.vue → 判断
```

---

## §页面模板 — 新建页面时用

**直接复制 DESIGN_SYSTEM.md §4.6 的完整代码块。** 包含：
- 操作区（左 KPI + 右按钮）
- 筛选区（标签 + 搜索）
- 内容区（唯一滚动容器，flex:1 1 0 / min-height:0 / overflow-y:auto）
- 卡片网格（3n+1/3n+2/3n+3 微旋转）
- 空状态模板
- 按钮/徽标样式

**复制后改什么：**

| 改这里 | 改成 |
|--------|------|
| `.module-page` 类名 | 换成模块名 |
| KPI 字段 `v-for="k in kpis"` | 换成实际 KPI 数据 |
| 筛选标签文字 | 换成实际筛选项 |
| 卡片字段 `item.name/description/status` | 换成实际数据字段 |
| `.badge` 状态类 | 从 DESIGN_SYSTEM.md §1.3 选对应状态色 |
| 按钮颜色 `.btn-primary` 的 `background` | 换成对应模块色 `var(--c-xxx)` |

**如果不用卡片用表格：** 保留操作区和筛选区不变，把 `.cards` 换成 `<el-table>`，复制 DESIGN_SYSTEM.md §2.2 的表格 `:deep()` 代码块。

---

## §组件模板 — 做新组件时用

**不要自己设计。** 从 DESIGN_SYSTEM.md §3 选最接近的模板，复制 CSS/HTML 结构，改内容。

| 你要做 | 复制什么 | 在哪 |
|--------|---------|------|
| 内容卡片 | 拍立得卡片（带图钉伪元素，hover 归零旋转放大） | DESIGN_SYSTEM.md §3.1 |
| 信息面板 | 纸艺卡片（更扁更轻，无图钉） | §3.2 |
| 统计数字 | KPI 卡（菱形色块 + `~` 水印 + Caveat 30px） | §3.3 |
| 状态标签 | Badge（边框+背景+文字三要素，5 种状态色） | §3.4 |
| 筛选切换 | 筛选标签（透明→hover 变黑→active 白底黑框） | §3.5 |
| 操作按钮栏 | 操作栏（flex space-between，左组+右组） | §3.6 |
| 空数据提示 | 空状态（居中图标+"暂无数据"+操作按钮） | §3.7 |
| 加载中 | 骨架屏 el-skeleton（禁止全屏 spinner） | §3.7 |
| 请求失败 | 错误状态（图标+错误信息+"重试"按钮） | §3.7 |
| 设置项列表 | 数据行（flex label 120px + value） | §3.8 |

---

## §基础原子 — 改 Element Plus 组件时用

**DESIGN_SYSTEM.md §2 每个组件都有可复制的 `:deep()` 代码块。** 直接复制，不改结构，只调颜色/尺寸。

| 要改 | 复制哪个代码块 | 注意 |
|------|--------------|------|
| 按钮颜色 | §2.1 的 `.el-button--primary` | 背景换成模块的 `var(--c-xxx)` |
| 表格行样式 | §2.2 的完整表格块 | 表头渐变 + 虚线行分隔 + 斑马纹 |
| 弹窗标题/按钮栏 | §2.3 的完整弹窗块 | 标题 Caveat 20px，底部按钮右对齐 |
| 输入框边框/focus | §2.4 的完整输入框块 | focus 变黄 `var(--app-highlight)`，不是蓝 |
| 表单标签/错误态 | §2.4 的表单块 | 错误文字在输入框下方，不动布局 |
| 状态 Badge | §2.5 的 Badge 块 | 选一个状态类名复制，改模块名前缀 |

---

## §视觉皮肤 — 改全局风格时用

所有变量在 `tokens.css`，使用指南在 DESIGN_SYSTEM.md §1。

| 要改 | 去哪查 | 用什么变量 |
|------|--------|-----------|
| 页面背景色 | §1.1 + §4.2 | `var(--paper)` + 点阵纸纹 |
| 模块主色调 | §1.2 | `var(--c-dashboard/device/element/...)` |
| 成功/失败/告警色 | §1.3 | `var(--app-status-success/danger/warning-*)` |
| 标题/正文/代码字体 | §1.4 | `var(--app-font-display)` / `var(--app-font)` / `var(--app-font-mono)` |
| 卡片/按钮圆角 | §1.5 | `var(--app-radius-md/sm)` — 不对称，禁止 50px |
| 卡片/弹窗阴影 | §1.6 | `var(--app-shadow-sm/md/lg)` — 扁平投影，0 模糊半径 |
| 间距 | §1.7 | `var(--app-space-xs/sm/md/lg/xl/2xl)` — 禁止随意值 |
| 动效时长 | §1.8 | `var(--app-duration-fast)` (0.12s) / `--app-duration` (0.15s) / `--app-duration-slow` (0.25s) |

---

## §快速对照：模块色映射

每个模块有自己的主题色，按钮/图标/边框装饰统一用它：

| 模块 | 变量 | 色值 |
|------|------|------|
| dashboard | `--c-dashboard` | `#F7C948` |
| device-pool | `--c-device` | `#6BCB77` |
| element-locator | `--c-element` | `#A78BFA` |
| case-manager | `--c-case` | `#4ECDC4` |
| test-runner | `--c-runner` | `#FFB5A7` |
| report-generator | `--c-report` | `#7C6F83` |
| ai-assistant | `--c-ai` | `#E879F9` |
| workflow | `--c-workflow` | `#89CFF0` |

---

## §做完之后：自检

```
[ ] 构建通过  cd frontend && npx vite build --mode development
[ ] 颜色全用 var(--xxx)，无硬编码色值
    grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" frontend/src/modules/ --include="*.vue" | grep -v tokens
[ ] 页面可纵向滚动（缩小浏览器窗口验证）
[ ] 卡片网格有 nth-child 微旋转
[ ] 页面背景有点阵纸纹
[ ] 空数据 / 加载中 / 出错 三个状态都有处理
[ ] 圆角不对称（无 50px/16px/20px 对称圆角）
[ ] 无 backdrop-filter: blur()
[ ] 无旧色值 #4a4e69 #9a8c98
[ ] 新 .vue 文件 ≤ 500 行
[ ] 文件位置正确：modules/{domain}/components/{Name}.vue
```
