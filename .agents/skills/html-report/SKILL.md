---
name: html-report
description: |
  HTML 报告生成器 — 为所有 skill 提供统一的 animal-island-ui 设计规范，确保项目内所有 HTML 输出（方案文档、分析报告、测试报告、质量报告、架构图等）视觉风格一致。
  包含完整 design token、26 组件样式规格、阴影系统、硬性规则和自包含 HTML 模板。
  Keywords: HTML报告, 设计规范, design token, animal-island-ui, 配色, 字体, 圆角, 阴影, 动画, 报告模板, 方案文档, 分析报告
  Trigger: 任何 skill 需要输出 HTML 报告/方案文档/分析文档/流程图时，必须加载 references/PROMPT.md 获取设计规范。
---

# HTML Report — animal-island-ui 设计规范与 HTML 报告生成

**定位**: 本项目所有 HTML 报告的**唯一权威设计规范来源**。

任何 skill（auto-dev、feature-analysis、code-health-check、architecture-review、quality-gate、functional-testing）生成 HTML 报告时，必须遵循本 skill 的规范。

**核心资产**: `references/PROMPT.md` 包含完整的 design token、26+ 组件样式规格、阴影系统、14 条硬性规则和自包含 HTML 生成提示词。

---

## 加载时机

| 触发场景 | 加载内容 | 说明 |
|---------|---------|------|
| 任何 skill 需要输出 HTML 报告 | `references/PROMPT.md` | 获取完整 design token |
| 用户要求"生成 HTML 报告/方案文档" | 完整 SKILL.md + `references/PROMPT.md` | 获取规范和模板 |
| 新 skill 集成 HTML 输出能力 | `references/PROMPT.md` | 参考规范，在关联文件表中注册 |
| 检查已有 HTML 是否符合规范 | `references/PROMPT.md` HARD RULES 部分 | 逐条对照 14 条硬性规则 |

---

## Design Token 速查

以下是从 PROMPT.md 提取的核心 token，供快速参考。完整规范见 `references/PROMPT.md`。

### 调色板

```
Primary teal:   #19c8b9 / hover #3dd4c6 / active #11a89b
Text:           headings #794f27 / body #725d42 / secondary #9f927d / muted #8a7b66
Background:     page #f8f8f0 / card rgb(247,243,223) / disabled #f0ece2
Border:         default #c4b89e / hover #a89878 / strong #9f927d
Status:         success #6fba2c / warning #f5c31c / error #e05a5a
Focus:          #ffcc00（⚠️ 禁止用冷蓝 #0066ff）
```

### 字体

```
Display:  Nunito (weight 600-900, letter-spacing 0.02em)
Body:     Nunito, 'Noto Sans SC', -apple-system, 'PingFang SC', sans-serif
          (weight 500, letter-spacing 0.01em)
Code:     'SF Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace (weight 600)
```

### 圆角

```
sm:   12px    — 交互元素最小值
base: 18px    — 卡片/容器
lg:   24px    — 大容器
pill: 50px    — 按钮/标签
```

### 阴影

```
3D pixel-stack:  0 5px 0 0 #bdaea0     — 仅 primary/danger 按钮
Soft elevation:  0 2px 4px 0 rgba(61,52,40,0.06)  — default/dashed/text/link 按钮
Card:            NO box-shadow           — hover 时 translateY(-2px)
```

### 动画

```
easing:   cubic-bezier(0.4, 0, 0.2, 1)
duration: fast 0.15s / base 0.25s / slow 0.35s
```

---

## 硬性规则（14 条，违反即不合格）

生成任何 HTML 报告后，必须逐条对照：

| # | 规则 | 禁止 | 正确 |
|---|------|------|------|
| 1 | 配色 | `#000` / `#111` / `#fafafa` / `#f5f5f5` | `#794f27` / `#725d42` / `#f8f8f0` / `rgb(247,243,223)` |
| 2 | 聚焦环 | `#0066ff` 等冷蓝色 | `#ffcc00` (Input/Switch/Checkbox) 或 `#19c8b9` (Button) |
| 3 | 圆角 | 0px 尖角 | 交互元素最小 12px |
| 4 | 背景色 | 冷灰色系 | 暖木色/羊皮纸色系 |
| 5 | 阴影 | 非 primary 按钮用 3D 像素堆叠 | 非 primary 用软阴影 |
| 6 | Modal | 圆角矩形替代 blob | 使用 SVG `clip-path: url(#animal-modal-clip)` |
| 7 | Title | 渲染为 blob/pill/矩形块 | 使用 heraldic ribbon 样式 |
| 8 | Card title | `<Card type="title">`（已废弃） | 使用 `<Title>` 组件 |
| 9 | 字体 | 系统字体 | 引入 Nunito + Noto Sans SC Google Fonts |
| 10 | 字重 | < 400 的字重 | body 500, heading 600-900 |
| 11 | 动画 | 硬切动画、linear | `cubic-bezier(0.4, 0, 0.2, 1)` 0.15-0.35s |
| 12 | Modal title | 与 `<Title>` 组件混淆 | Modal 的 `title` prop 是普通字符串 |
| 13 | 组件优先 | 手写 HTML 替代已有组件 | 优先用 animal-island-ui 组件 |
| 14 | 自包含 | 依赖外部 CSS/JS 框架 | 所有 CSS 内联在 `<style>` 块 |

---

## 标准 HTML 报告模板

### 文件骨架

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{报告标题}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      /* 从 PROMPT.md 的 :root 块复制完整 design token */
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Nunito, 'Noto Sans SC', -apple-system, 'PingFang SC', sans-serif;
      font-weight: 500;
      letter-spacing: 0.01em;
      background: #f8f8f0;
      color: #725d42;
      line-height: 1.6;
    }
    /* 报告专属样式 */
  </style>
</head>
<body>
  <!-- 报告内容 -->
</body>
</html>
```

### 布局规范

| 区域 | 规范 |
|------|------|
| 页面宽度 | 最大 1100-1200px，居中，padding 32-48px |
| KPI 摘要卡片 | 4 列 grid，装饰圆点 + 彩色左边框 |
| 表格 | 暖色表头渐变 + 斑马纹行 + 虚线分隔 `border-bottom: 1px dashed` |
| 结论区域 | 卡片 + 左边框色带（teal=结论，blue=上下文） |
| Footer | 虚线分隔线 + 生成时间戳 |

---

## 与其他 Skill 的关系

```
html-report (本 skill)
  │  design token 权威来源
  │  references/PROMPT.md
  │
  ├── 被以下 skill 消费:
  │   ├── feature-analysis     → Phase 3 报告生成
  │   ├── architecture-review  → Phase 3 HTML 报告
  │   ├── code-health-check    → Phase 3 输出报告
  │   ├── quality-gate         → Phase 5 输出矩阵报告
  │   ├── functional-testing   → 测试报告生成
  │   └── auto-dev             → Phase 5 交付 HTML 报告
  │
  └── 独立使用:
      └── 用户直接要求"生成 animal-island-ui 风格的 HTML 页面"
```

**html-report 本身不依赖任何其他 skill**，是纯规范层（leaf node）。

---

## HTML 输出自检清单

生成任何 HTML 报告后，必须逐条检查：

```
[ ] 配色: 无 #000 / #fafafa / #0066ff
[ ] 字体: 包含 Nunito + Noto Sans SC CDN 链接
[ ] 圆角: 所有交互元素 >= 12px
[ ] 阴影: 非 primary 按钮无 3D 像素堆叠阴影
[ ] 动画: cubic-bezier(0.4, 0, 0.2, 1)
[ ] 自包含: 所有 CSS 内联，不依赖外部框架
[ ] 响应式: @media (max-width: 768px) 移动端适配
[ ] 打印: @media print 去除背景色和阴影
```

---

## 关联文件

| 文件 | 用途 |
|------|------|
| `references/PROMPT.md` | 完整 design token + 26 组件样式规格 + self-contained HTML 生成提示词 |
| `.Codex/rules/animal-island-ui.md` | 动森 UI 组件 API 速查（项目内 npm 包用法） |
