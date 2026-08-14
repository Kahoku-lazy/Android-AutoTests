# Doodle Craft 组件规格（像素级）

> 唯一真相源：`frontend/DESIGN_SYSTEM.md`（设计系统）+ `frontend/src/shared/styles/tokens.css`（令牌）。
> **令牌值以 tokens.css 为准**；新增/修改组件时同步更新本文件。

共 20 个组件：基础 UI 原子层（Element Plus 覆盖）10 个 + 组件层（业务组件）10 个。

## 状态色（Tag / Badge / 时间线 / 状态图标共用）

| 状态 | 边框/图标 | 背景 | 文字 |
|------|----------|------|------|
| 成功/在线 | `#6BCB77` | `#C8F5D0` | `#2d7a2d` |
| 危险/失败 | `#FFB5A7` | `#FFE0DB` | `#a03030` |
| 紫色/锁定 | `#A78BFA` | `#E8DDF8` | `#5a3fa0` |
| 警告/等待 | `#F7C948` | `#FFF9E0` | `#7a5a10` |
| 离线/禁用 | `#d4d8dc` | `#f0ede8` | `#999` |

---

## 一、基础 UI 原子层（Element Plus 覆盖，走 `--el-*` / `:deep()`）

### 1. Button 按钮

| 属性 | 值 |
|---|---|
| 圆角 | `4px 8px 4px 8px`（`--app-radius-sm`） |
| 边框 | `2px solid var(--ink)` |
| 字号/字重 | 11px / 700 |
| padding | `6px 16px` |
| 背景/文字 | `#fff` / `var(--ink)` |
| hover | 背景 `#FFE066`（`--app-highlight`），位移 `translate(1px,1px)` |
| active | 位移归零 `translate(0,0)` |
| disabled | 透明度 0.5，禁止点击 |
| primary | 背景 `var(--c-dashboard)`，文字 `var(--ink)` |
| danger | 背景 `var(--app-status-danger)`，白字（只在确认弹窗用） |

**约束**：一个操作区内最多一个 primary，其余 default。危险操作用 danger 但放确认弹窗。

### 2. Table 表格

| 属性 | 值 |
|---|---|
| 表头背景 | `linear-gradient(180deg, var(--app-bg-subtle), rgba(248,246,242,0.4))` |
| 行分隔 | `1px dashed var(--app-border-lighter)` |
| 斑马纹 | `nth-child(even)` 微妙底色 `rgba(248,246,242,0.4)` |
| hover 行 | 浅 teal `rgba(25,200,185,0.05)` |
| 空态 | 居中：图标 + "暂无数据" |
| 加载 | `v-loading` + 骨架行 |
| 边框 | 无外框，内部虚线分隔 |

**约束**：只在页面主内容区/Tab 面板；需 `max-height` + 固定表头；禁止嵌在卡片里。

### 3. Dialog / Modal 弹窗

| 属性 | 值 |
|---|---|
| 宽度 | sm 420px / md 520px / lg 720px |
| 标题 | 左对齐，Caveat 20px / 700，下划线分隔 |
| 内容区 | padding `--app-space-md`，无内部滚动 |
| 底部按钮 | 右对齐，取消左 / 确认右 |
| 遮罩 | `rgba(0,0,0,0.3)`，无模糊 |
| 圆角 | `--app-radius-md` |

**约束**：弹窗内不放表格；弹窗内表单宽度 ≤520px。

### 4. Form / Input 表单与输入

| 属性 | 值 |
|---|---|
| label 对齐 | 左对齐，宽 80 / 100 / 120px 三档 |
| 输入框高 | sm 32px / md 40px / lg 48px |
| 输入框圆角 | `4px 8px 4px 8px` |
| 输入框边框 | `2px solid var(--ink)`，focus 变 `#FFE066` |
| placeholder | `#999`，字重 400 |
| 校验错误 | 边框 `#FFB5A7`，错误文字在输入框下方 |

**约束**：表单不放卡片网格；弹窗内单列；错误提示不动布局。

### 5. Tag / Badge 标签

| 属性 | 值 |
|---|---|
| 字号/字重 | 10px / 700 |
| 圆角 | `3px 6px 3px 6px` |
| 边框 | `1.5px solid var(--ink)` |
| 背景/文字 | 按状态色（见上表） |
| padding | `2px 7px` |

### 6. Pagination 分页

右对齐，放表格下方。简化版（只显示页码 + 箭头），不显示总数下拉。

### 7. Tabs 标签页

激活项下划线 `2px solid var(--ink)`；内容区 padding-top `--app-space-md`。

### 8. Select 下拉

下拉选项 hover `#FFE066`；选中项加粗。

### 9. Cascader 级联

⚠️ `emitPath` 默认 `true`，必须显式设 `emitPath: false`。

### 10. el-menu 侧边栏菜单

激活项背景 `var(--c-dashboard)`。

---

## 二、组件层（业务组件，边框 + 背景 + 文字三要素）

### 11. 拍立得卡片 `.card`

```
边框:  2.5px solid var(--ink)
背景:  #fff
文字:  var(--ink)
圆角:  6px 10px 6px 10px
阴影:  2px 3px 0 rgba(0,0,0,0.05)
装饰:  ::before 图钉（9×9 径向渐变圆，居中置顶）
hover: rotate(0deg) scale(1.03)，阴影加深
```

**用途**：模块内容卡片、数据摘要卡片。

### 12. 纸艺卡片 `.card-info`

```
边框:  2.5px solid var(--ink)
背景:  #fff
圆角:  4px 10px 6px 8px
阴影:  2px 2px 0 rgba(0,0,0,0.04)
hover: translate(1px,1px)，阴影收窄
```

**用途**：信息提示、次要面板、嵌套内层卡片（比拍立得更扁更轻，去掉图钉）。

### 13. KPI 统计卡 `.kpi-card`

```
边框:  3px solid var(--ink)
背景:  #fff
数字:  Caveat 30px / 700（标签 Quicksand 13px）
圆角:  4px 10px 6px 8px
阴影:  2px 3px 0 rgba(0,0,0,0.04)
装饰:  顶部菱形色块（10×10，rotate 45°，2px solid var(--ink)）
       底部 "~" 水印（Caveat 17px，opacity 0.12）
```

**用途**：仪表盘统计数字、操作区摘要条。

### 14. 状态 Badge `.badge`

```
边框:  1.5px solid var(--ink)
背景:  状态对应背景色
文字:  状态对应文字色，10px / 700
圆角:  3px 6px 3px 6px
```

### 15. 筛选标签 `.filter-tab`

```
default: 背景 transparent，文字 #999，边框 2px solid transparent
hover:   文字 var(--ink)
active:  背景 #fff，文字 var(--ink)，边框 2px solid var(--ink)
圆角:    4px 8px 4px 8px
字号:    11px / 700
```

### 16. 操作栏 `.action-bar`

```
边框:  无
背景:  transparent
布局:  flex，左操作组 + 右操作组（space-between）
间距:  gap --app-space-sm
按钮:  11px / 700，主操作一个 primary
```

### 17. 空状态 `.empty-state`

```
布局:  居中 text-align center，padding 60px 20px
图标:  模块色，opacity 0.5，64×64
文字:  #999，14px，"暂无数据"
按钮:  可选，文字下方 gap 12px
```

### 18. 加载骨架屏

```
列表页: el-skeleton + 5 行动画行
详情页: el-skeleton + 标题/段落/图片占位
禁止:   全屏 spinner
```

### 19. 错误状态

```
布局:  居中，padding 40px 20px
图标:  #FFB5A7
文字:  #a03030，14px，错误信息摘要
按钮:  "重试" default 样式，文字下方
禁止:  白屏或无反馈
```

### 20. 数据行

```
边框:  下边框 1px dashed var(--app-border-lighter)
背景:  transparent
布局:  flex，label 左对齐 120px + value 弹性宽度
hover: 背景 var(--app-bg-subtle)
```

**用途**：设置项、配置列表（表格行和卡片之外的第三种展示模式）。
