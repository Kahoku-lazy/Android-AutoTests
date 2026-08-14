# Doodle Craft 页面层 — 布局骨架与滚动规则

> 来源：`frontend/DESIGN_SYSTEM.md` §四（已瘦身，页面规则现以此文件为准）。令牌值以 tokens.css 为准。

## 4.1 标准页面骨架

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

自上而下五段：侧边栏+顶栏 → 操作区 → 筛选区 → 主内容区（唯一纵向滚动）→ 页脚。

## 4.2 页面背景（点阵纸纹）

```css
background: radial-gradient(circle, var(--dot) 0.6px, transparent 0.6px);
background-size: 15px 15px;
background-color: var(--paper);
```

所有页面统一点阵纸纹，**禁止纯色背景**。

## 4.3 卡片网格微旋转

```css
.cards > :nth-child(3n+1) { transform: rotate(-0.6deg); }
.cards > :nth-child(3n+2) { transform: rotate(0.4deg); }
.cards > :nth-child(3n+3) { transform: rotate(-0.3deg); }
.cards > :hover { transform: rotate(0deg) scale(1.03); z-index: 5; }
```

卡片区统一使用。**禁止网格中卡片全部 0deg 排排坐**。

## 4.4 滚动规则

| 区域 | 滚动 | 规则 |
|------|:--:|------|
| 页面主内容区 | 纵向 | `flex: 1 1 0; min-height: 0; overflow-y: auto` |
| 表格 | 横向 | `overflow-x: auto` + 固定表头 |
| 卡片 | 禁止 | 卡片本身不设滚动，溢出裁剪或外部容器滚动 |
| 弹窗内容 | 禁止 | 弹窗不设内部滚动 |

**关键**：禁止任何中间层出现 `overflow: hidden`，会导致内容被裁剪。翻车记录：`info-card` 残留 `overflow:hidden` + `el-tabs__content` 的 `overflow:hidden` 三层裁剪。

## 4.5 内容区 Flex 子项规则

```css
.content-area {
  flex: 1 1 0;        /* 必须，占满剩余高度 */
  min-height: 0;      /* 必须，覆盖 min-height:auto */
  overflow-y: auto;   /* 必须，唯一纵向滚动容器 */
}
```

三个属性缺一不可，缺了内容溢出时页面无法滚动。

## 4.6 内容区宽度规则

**禁止在全局样式对内容区设 `max-width` 并居中**，各模块自己决定。

| 场景 | 是否 max-width | 理由 |
|------|:--:|------|
| 仪表盘、设备管理（卡片网格/表格/图表） | ❌ | 内容密度高、多列布局 |
| 元素定位（截图 + 元素树并排） | ❌ | 左右分栏，限宽会压操作区 |
| 长文本阅读、Markdown 渲染 | ✅ 700–900px | 阅读舒适度 |
| 表单填写页 | ⚠️ 可选 800px | 光标移动距离 |

翻车记录：全局 `.doc-body` 设 `max-width: 1600px; margin: 0 auto`，导致大屏（2560px+）两侧各 ~480px 空白，已移除。

## 4.7 标准页面模板（3 变体）

| 你的页面是…… | 用哪个变体 | 示例模块 |
|------------|:--:|------|
| 卡片网格 + KPI 统计 | 变体 A | dashboard、device-pool |
| 表格列表 + 筛选栏 | 变体 B | report-generator、test-runner |
| 左侧树/面板 + 右侧内容 | 变体 C | element-locator、case-manager |

> 每个变体复制后改 KPI 字段 / 筛选标签 / 卡片字段 → 完成。表格页把 `.cards` 换成 `el-table`。

## 4.8 数据加载骨架

所有 fetch 页面用同一骨架（script + template），只改标注「← 改这里」的部分：导入 api、数据变量名、API 调用、响应字段、错误文案、模板内容。

> 完整代码模板可从 git 历史恢复（原 DESIGN_SYSTEM.md §4.7）。
