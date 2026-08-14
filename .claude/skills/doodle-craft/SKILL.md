# Doodle Craft 主题 — 前端 UI 开发与维护迭代

> 极简几何 · 粗线涂鸦 · 彩绘卡通 · 手稿纸
> 令牌唯一真相源：`frontend/src/shared/styles/tokens.css`
> 风格约束与验收：`frontend/DESIGN_SYSTEM.md`
> 前端编码规范（嵌套深度 / z-index / 文件组织 / 脚手架）：`.claude/rules/frontend.md`

本技能用于**做页面 / 做组件 / 改样式**，以及**维护迭代 Doodle Craft 主题**。

## 核心原则

1. **复制，不发明**：每个 UI 元素都有预定义模板。复制最接近的模板，改内容字段，不从零设计。
2. **令牌，不硬编码**：颜色/间距/圆角/阴影用 `var(--xxx)`，不写字面量。例外：ECharts/Canvas JS 配置用字面量。
3. **四层，不越界**：页面骨架 → 基础原子（Element Plus）→ 业务组件（卡片/Badge/KPI）→ 视觉令牌（tokens.css），上层不反向侵入下层。

## 参考文件

| 文件 | 内容 | 何时用 |
|------|------|--------|
| `frontend/src/shared/styles/tokens.css` | 设计令牌唯一真相源 | 改令牌值 |
| `frontend/DESIGN_SYSTEM.md` | 风格约束（硬编码值）+ 验收前端设计 | 验收 / 查约束 |
| `references/tokens.md`（本技能） | 视觉皮肤层：色板 / 模块色 / 状态色 / 字号 / 字体 / 圆角 / 阴影 / 间距 / 动效 / 颜色使用规则 | 改视觉属性时查精确值 |
| `references/components.md`（本技能） | 20 个组件像素级规格（Element Plus 原子 10 + 业务组件 10） | 做/改组件时查精确值 |
| `references/layout.md`（本技能） | 页面层：骨架 / 点阵背景 / 微旋转 / 滚动规则 / flex 规则 / 宽度规则 / 页面变体 | 改布局时查规则 |

## 工作流

先判定你在做什么，再查对应参考：

| 你要做什么 | 查哪 | 改哪里 |
|-----------|------|--------|
| 新建页面 | `references/layout.md` §4.7 页面变体 | 复制骨架变体，改字段 |
| 加卡片 / 做数据展示 | `references/components.md` §二 业务组件 | 复制组件规格 |
| 改按钮/表格/弹窗/表单/输入框 | `references/components.md` §一 基础原子 | 复制 `:deep()` 块，只调色/尺寸 |
| 改颜色/字体/间距/圆角/阴影/动效 | `references/tokens.md` | `tokens.css` 对应 `--app-*` / `--el-*` 变量 |
| 改页面布局 / 排查不可滚动 | `references/layout.md` | 组件 `scoped CSS`（用 `var(--*)`） |
| 新增设计规则 | — | 同步 `DESIGN_SYSTEM.md` + `tokens.css` |

**验证**：改完确认 `tokens.css ↔ DESIGN_SYSTEM.md ↔ 组件` 三者一致，无硬编码色值/字号残留。

## 8 模块色（主题一部分，勿随意改动）

| 模块 | CSS 变量 | 色值 |
|------|----------|------|
| dashboard | `--c-dashboard` | `#F7C948` 柠黄 |
| device-pool | `--c-device` | `#6BCB77` 薄荷绿 |
| element-locator | `--c-element` | `#A78BFA` 薰衣草紫 |
| case-manager | `--c-case` | `#4ECDC4` 青绿 |
| test-runner | `--c-runner` | `#FFB5A7` 桃粉 |
| report-generator | `--c-report` | `#7C6F83` 灰紫 |
| ai-assistant | `--c-ai` | `#E879F9` 柔粉紫 |
| workflow | `--c-workflow` | `#89CFF0` 天蓝 |

> 另有语义色 `--app-module-*` 系列与上述 8 色对应（如 `--app-module-green` = device-pool）。改模块色时两处同步。

## 平台图标映射（侧边栏 Lucide）

侧边栏使用 Lucide（`data-lucide` + `window.lucide.createIcons()`）。实际映射见 `frontend/src/shared/components/sidebarNavConfig.ts`，参考：

```javascript
const NAV_ICONS = {
  dashboard:       'layout-dashboard',
  device_pool:     'smartphone',
  element_locator: 'crosshair',
  case_manager:    'layers',
  test_runner:     'play-circle',
  report:          'file-bar-chart',
  ai_assistant:    'bot',
  workflow:        'git-branch',
  digital_human:   'user-round',
}
```

> 注意：模块内业务组件用 `shared/icons/index.ts` 的 `makeIcon` 自定义 SVG，与侧边栏 Lucide 是两套体系。改图标时先确认目标组件用哪套。

## 做完之后：自检

```
[ ] 构建通过  cd frontend && npx vite build --mode development
[ ] 颜色全用 var(--xxx)，无硬编码色值
[ ] 字号只用 6 档（--app-size-*），无 10px/11px
[ ] 圆角不对称（无 50px/16px/20px 对称圆角）
[ ] 阴影扁平（无模糊 shadow）
[ ] 间距用刻度变量（无 15px/20px 随意值）
[ ] 页面可纵向滚动（缩小窗口验证）
[ ] 卡片网格有 nth-child 微旋转
[ ] 页面背景有点阵纸纹
[ ] 空/加载/错三态齐备
[ ] 无 backdrop-filter: blur()
[ ] 无旧色值 #4a4e69 #9a8c98
[ ] 新 .vue 文件 ≤ 500 行
```

> 完整分组验收标准见 `DESIGN_SYSTEM.md` §二；工程门禁（布局/契约/可达性/四态）用 `vue-frontend-check` skill。
