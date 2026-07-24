# Paper × Polaroid 设计系统

> 全平台统一视觉语言。以下规范适用于所有业务模块（AI 助手除外）。

---

## 一、色板

### 基础 Token

| Token | 色值 | 用途 |
|-------|------|------|
| `--app-ink` | `#2d2d2d` | 主墨色 — 文字、图标、实色边框 |
| `--app-ink-muted` | `#999` | 弱化墨色 — 辅助文字、占位符 |
| `--app-paper` | `#fefcf6` | 纸底色 |
| `--app-paper-dot` | `#d4cdc0` | 纸纹圆点 |
| `--app-border-light` | `#e8ecf1` | 浅边框 |
| `--app-border-lighter` | `#f0ede8` | 更浅边框 |
| `--app-bg-subtle` | `#f8f6f2` | 微妙底色 |
| `--app-highlight` | `#FFE066` | 高亮黄 — hover 背景、页脚 |
| `--app-live` | `#f87171` | 活动指示红 |

### 状态色

| Token | 色值 | 用途 |
|-------|------|------|
| `--app-status-success` | `#6BCB77` | 在线 / 成功 |
| `--app-status-success-bg` | `#C8F5D0` | 成功背景 |
| `--app-status-success-text` | `#2d7a2d` | 成功深色文字 |
| `--app-status-danger` | `#FFB5A7` | 危险 / 失败 |
| `--app-status-danger-bg` | `#FFE0DB` | 危险背景 |
| `--app-status-danger-text` | `#a03030` | 危险深色文字 |
| `--app-status-purple` | `#C9B6F2` | 紫色强调 |
| `--app-status-purple-bg` | `#E8DDF8` | 紫色背景 |
| `--app-status-purple-text` | `#5a3fa0` | 紫色深色文字 |
| `--app-status-purple-border` | `#A78BFA` | 紫色边框 |
| `--app-status-warning-bg` | `#FFF9E0` | 警告背景 |
| `--app-offline` | `#d4d8dc` | 离线灰 |
| `--app-accent-blue` | `#89CFF0` | 设备管理模块蓝 |

### 模块对应色

| 模块 | 强调色 | 用途 |
|------|--------|------|
| dashboard | `app-yellow` `#F4D35E` | 仪表盘卡片、统计数字 |
| device-pool | `app-green` `#6BCB77` | 在线状态、操作按钮 |
| element-locator | `purple` `#b39ef3` | 树节点选中、XPath 最佳匹配 |
| case-manager | `app-teal` `#19c8b9` | 用例卡片、步骤 |
| test-runner | `app-pink` `#FFB5A7` | 执行中任务、进度 |
| report-generator | `brown` `#8b7355` | 报告表格、文件 |
| ai-assistant | `app-orange` `#f7a8c4` | AI 对话（独立主题见 animal-island-ui） |
| workflow | `app-blue` `#889df0` | 工作流画布 |

---

## 二、边框 & 圆角

- **实色边框**：`2.5px solid var(--app-ink)` — 卡片/面板外框
- **薄边框**：`1.5px solid var(--app-border-light)` — 内部元素分隔
- **圆角**：不对称 `6px 10px 6px 10px`（拍立得风格）— 卡片、面板
- **按钮/输入框圆角**：`4px 8px 4px 8px`
- **小 badge 圆角**：`3px 6px 3px 6px`

---

## 三、字体

| 用途 | 字体 | 规格 |
|------|------|------|
| 页面标题 | `Caveat`, cursive | 24px / 700 |
| 段落标题 | `Caveat`, cursive | 18-20px / 700 |
| UI 正文 | `Inter` / `PingFang SC` | 11-14px / 400-700 |
| 代码/等宽 | `JetBrains Mono` / `Fira Code` / `Consolas` | 9-13px / 500-600 |
| 数字统计 | `Caveat` + `Quicksand` | 24-28px / 700-800 |

---

## 四、组件

### 卡片（所有容器面板）

```css
.card {
  background: #fff;
  border: 2.5px solid var(--app-ink);
  border-radius: 6px 10px 6px 10px;
  box-shadow: 2px 3px 0 rgba(0, 0, 0, 0.05);
  padding: 8px 8px 30px 8px; /* 底部留空给图钉 */
  position: relative;
}
/* 图钉 */
.card::before {
  content: '';
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 9px;
  height: 9px;
  background: radial-gradient(circle, #e8e0d5 30%, #c0b8a8 60%, #a09080 100%);
  border-radius: 50%;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.08);
}
.card:hover {
  transform: rotate(0deg) scale(1.03);
  box-shadow: 2px 4px 0 rgba(0, 0, 0, 0.08);
}
```

### 按钮

```css
.btn {
  font-size: 10-12px;
  font-weight: 700;
  border: 2px solid var(--app-ink);
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  color: var(--app-ink);
  cursor: pointer;
  font-family: inherit;
  transition: all 0.12s;
}
.btn:hover { background: var(--app-highlight); }
.btn-primary { background: var(--app-ink); color: #fff; }
.btn-sm { font-size: 9px; padding: 3px 8px; }
```

### Badge / 标签

```css
.badge {
  font-size: 9-10px;
  font-weight: 700;
  padding: 2px 7px;
  border: 1.5px solid var(--app-ink);
  border-radius: 3px 6px 3px 6px;
  display: inline-block;
}
.badge-green  { background: var(--app-status-success-bg); color: var(--app-status-success-text); }
.badge-pink   { background: var(--app-status-danger-bg);  color: var(--app-status-danger-text); }
.badge-purple { background: var(--app-status-purple-bg);  color: var(--app-status-purple-text); }
.badge-gray   { background: var(--app-border-lighter);    color: var(--app-ink-muted); }
.badge-yellow { background: var(--app-status-warning-bg); color: #7a5a10; }
```

### 筛选标签

```css
.filter-tab {
  padding: 4px 12px;
  font-size: 10px;
  font-weight: 700;
  color: var(--app-ink-muted);
  background: transparent;
  border: 2px solid transparent;
  border-radius: 4px 8px 4px 8px;
  cursor: pointer;
}
.filter-tab:hover { color: var(--app-ink); border-color: var(--app-border-light); }
.filter-tab.active { color: var(--app-ink); background: #fff; border-color: var(--app-ink); }
```

---

## 五、页面布局

```
┌──────────────────────────────────────────┐
│ WorkbenchHeader (标题 + 图标 + 操作按钮)    │
├──────────────────────────────────────────┤
│ Tab 栏 / 筛选栏 (可选)                     │
├──────────────────────────────────────────┤
│                                          │
│   卡片网格 / 表格 / 三栏布局                │
│   (scrollable)                           │
│                                          │
├──────────────────────────────────────────┤
│ Footer: 黄色便签条                         │
│ background: #FFE066; color: #5a4e20;     │
│ font: Caveat, 12px                       │
└──────────────────────────────────────────┘
```

**页面背景**：
```css
.page {
  background:
    radial-gradient(circle, var(--app-paper-dot) 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: var(--app-paper);
}
```

**卡片网格微旋转**（拍立得错落感）：
```css
.cards > :nth-child(3n+1) { transform: rotate(-0.8deg); }
.cards > :nth-child(3n+2) { transform: rotate(0.5deg); }
.cards > :nth-child(3n+3) { transform: rotate(-0.4deg); }
.cards > :hover { transform: rotate(0deg) scale(1.03); z-index: 5; }
```

---

## 六、CSS 变量安全边界

CSS 变量 `var(--app-*)` 仅在 DOM 上下文中有效：

| 上下文 | CSS 变量 | 必须用字面量 |
|--------|:--:|:--:|
| `<style>` 块 / `.css` 文件 | ✅ | |
| 内联 `:style=""` | ✅ | |
| **ECharts / Canvas / SVG 库 JS 配置** | | ❌ `#xxx` |

> Canvas 渲染引擎不解析 CSS 变量。改 tokens.css 色值后，需同步更新对应 JS 渲染配置中的硬编码色值。

---

## 七、主题同步检查清单

实施或修改模块主题时，逐项确认：

- [ ] 色值全部来自 `tokens.css`，无新增硬编码 `#xxx`
- [ ] 边框 2.5px solid `--app-ink`（卡片/面板外框）
- [ ] 圆角 `6px 10px` 不对称（卡片）、`4px 8px`（按钮）
- [ ] 卡片有图钉 `::before` 伪元素
- [ ] 标题使用 `Caveat`，代码使用 `JetBrains Mono`
- [ ] 模块使用其对应的强调色（见 §一 模块对应色表）
- [ ] 页脚黄色便签条 `#FFE066`
- [ ] 背景纸纹 dot pattern
- [ ] ECharts/Canvas JS 配置中的颜色保留字面量
- [ ] 卡片网格微旋转
