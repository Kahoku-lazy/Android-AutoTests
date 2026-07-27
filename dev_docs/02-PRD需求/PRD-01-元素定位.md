# PRD-01 — 元素定位 (Element Locator)

> 关联需求大纲：[`需求大纲.md`](./需求大纲.md) §5.2
> 版本：v6.0 · 日期：2026-07-27

---

## 1. 功能定位

元素定位是 UI 自动化测试的感知层。用户在此连接设备、Dump UI 层级、选取界面元素、管理页面与元素库。页面由 4 个 Tab 构成：设备元素获取 → Android 元素管理 → Web 端元素 → API 接口。

---

## 2. 设计目录

```
frontend/src/modules/element-locator/
├── index.vue                         482 行 · 页面编排者（4 Tab 容器）
├── api.js                            158 行 · 数据层（35 端点）
├── store.js                          242 行 · Pinia 状态管理
├── routes.js                          14 行 · 路由定义
├── composables/
│   ├── useElementTree.js             549 行 · Android 页面树状态
│   ├── useWebGroupTree.js            273 行 · Web 分组树状态
│   └── useApiGroupTree.js            273 行 · API 分组树状态
└── components/
    ├── DeviceSelector.vue            145 行 · 设备选择器
    ├── ScreenshotView.vue            589 行 · 实时截图流 + Canvas 边界框
    ├── XPathCandidatePanel.vue       504 行 · XPath 候选 + 元素详情
    ├── PageElementsPanel.vue         790 行 · 元素列表 + 批量保存
    ├── ElementManager.vue            455 行 · Android 元素管理（页面树 + 表格）
    ├── ElementManager.css            703 行 · 三 Manager 共享样式
    ├── WebElementManager.vue        1072 行 · Web 元素管理（GroupTreePanel + 表格）
    └── ApiEndpointManager.vue        770 行 · API 端点管理（GroupTreePanel + 表格）
```

**架构特征**：L3 评级。四层分离但有违规 — store.js 和 3 个 composable 直接调用 ElMessage（业务逻辑层引用 UI 层）。跨模块通信通过 EventBus (`add-step-to-case`, `elements-saved`)，无直接跨模块 import。裸 client 调用已于 v6.0 全部收敛到 api.js。

---

## 3. 核心功能

### 3.1 设备元素获取 (Discovery Tab)

页面左侧手机截图 + Canvas 边界框叠加层（三种颜色：蓝色=普通，橙色=悬停，红色=选中）。中间 XPath 候选面板。右侧元素列表。

#### 3.1.1 设备选择

`DeviceSelector.vue` — 下拉框列出所有在线设备（ONLINE/BUSY），每项显示型号、分辨率、连接方式。选择设备后手动点击「连接」进入 observe 模式。30 秒内自动检测离线。当前设备离线时显示 ⚠️ 警告标记。

#### 3.1.2 实时截图流

`ScreenshotView.vue` — WebSocket `/ws/screenshot` 主通道推送 2fps 截图帧。REST `/elements/screenshot` 作为首帧兜底（避免 WebSocket 握手期间白屏）。断连后 ≤3 秒显示「截图流已断开」+ 倒计时自动重连，重连失败后显示手动重试按钮。

#### 3.1.3 Dump UI 层级

点击「Dump UI」→ POST `/elements/dump` → 返回完整 UI 层级树。每个交互元素自动生成最多 8 种 XPath 候选，按匹配数升序排列（count=1 排最前）。XML 截断容错处理，超时 30 秒提示。

#### 3.1.4 点击选取元素 + XPath 操作

点击 Canvas 边界框 → 元素选中（变红）→ `XPathCandidatePanel` 展示：元素属性（class/text/resource_id/bounds/clickable）+ XPath 候选列表（策略名 + 表达式 + 匹配数）。每条候选有 📋 复制 + ➕ 添加到用例按钮（通过 EventBus `add-step-to-case` 跨模块发送）。

#### 3.1.5 元素列表 + 批量保存

`PageElementsPanel.vue` — 可滚动元素行列表，每行有 checkbox + thumbnail 缩略图（CSS background-position 裁剪）+ XPath 信息。批量保存弹窗：选择目标页面 → 选择 XPath 策略 → 保存到 Element Manager。

### 3.2 Android 元素管理 (Manage Tab)

`ElementManager.vue` + `useElementTree.js` — 左侧自建页面树（el-tree + 右键菜单 + 长按拖拽 + 批选模式），右侧元素表格（AppTable + 7 列）。

#### 3.2.1 页面树管理

树形结构最大 5 层。右键菜单：新建子页面 / 重命名 / 删除 / 移动到。长按 500ms 激活拖拽。批选模式：勾选 → 批量移动。删除含元素的页面需二次确认「将同时删除该页面下的所有元素」。支持「全部清空」。

#### 3.2.2 元素表格

7 列：别名（行内编辑 blur/enter 保存）、XPath、class_name、text_val、resource_id、clickable 标签、is_test_point Switch。4 个筛选 Tab：全部 / 可点击 / 已命名 / 测试点。分页通过 `usePagination`（10/20/50/100）。表格头 7 色渐变（独立于 Doodle Craft 令牌的硬编码值）。

### 3.3 Web 元素管理 (Web Tab)

`WebElementManager.vue` + `useWebGroupTree.js` — 使用共享 `GroupTreePanel` 组件。右侧元素表格：name / locator_type（12 种彩色标签）/ locator_value / page_url / description / is_test_point。支持 JSON 批量导入 + page-flow 管理。

### 3.4 API 端点管理 (API Tab)

`ApiEndpointManager.vue` + `useApiGroupTree.js` — 使用共享 `GroupTreePanel` 组件。右侧表格：name / method（GET=绿/POST=紫/DELETE=红 等彩色标签）/ URL / description / is_test_point。新增/编辑弹窗支持 headers/request body/response body 的 JSON 编辑器。

---

## 4. 数据流

```
Pinia store (store.js)
  ├── devices[]         设备列表（来自 API）
  ├── elements[]        当前 dump 结果
  ├── actionable[]      可交互元素（过滤后）
  ├── selected          当前选中元素
  └── screenshotUrl     截图 URL（共享给 PageElementsPanel 缩略图）

Composables
  ├── useElementTree     页面树状态 → ElementManager
  ├── useWebGroupTree     Web 分组树状态 → WebElementManager
  └── useApiGroupTree     API 分组树状态 → ApiEndpointManager

index.vue
  ├── 4 Tab 容器        负责 Tab 切换 + EventBus emit
  ├── ScreenshotView     WebSocket + REST 双通道截图
  ├── XPathCandidatePanel  选中元素详情 + XPath 操作
  └── PageElementsPanel    批量勾选保存元素
```

### 跨模块通信

```
element-locator ──bus.emit('add-step-to-case')──→ case-manager (StepEditor)
element-locator ──bus.emit('elements-saved')──→   内部 (useElementTree)
```

---

## 5. 验收汇总

| 功能编号 | 功能名称 | 验收项 | 通过 | 未验证 |
|:--:|------|:--:|:--:|:--:|
| F-01-01 | 设备选择 | 5 | | 5 |
| F-01-02 | Dump UI 层级 | 6 | | 6 |
| F-01-03 | 实时截图流 | 7 | | 7 |
| F-01-04 | 点击截图选取元素 | 5 | | 5 |
| F-01-05 | XPath 候选操作 | 6 | | 6 |
| F-02-01 | Android 页面树管理 | 8 | | 8 |
| F-02-02 | Android 元素表格管理 | 7 | | 7 |
| F-02-03 | Web 元素管理 | 5 | | 5 |
| F-02-04 | API 端点管理 | 5 | | 5 |
| F-03-01 | EventBus 跨模块通信 | 4 | | 4 |
| **合计** | | **58** | **0** | **58** |

---

## 附录A：测试优先级

| 优先级 | 覆盖范围 | 验收时机 |
|:--:|------|------|
| P0 | F-01-01~F-01-05、F-02-01~F-02-02（核心交互） | 每次 MR 前 |
| P1 | F-02-03~F-02-04（Web/API 管理）、F-03-01（跨模块） | 发版前 |
| P2 | 边界条件、性能、异常场景 | 大版本前 |

## 附录B：实施状态

| 功能 | 状态 |
|------|:--:|
| 设备选择 + observe 连接 | ✅ |
| Dump UI + XPath 8 策略生成 | ✅ |
| 实时截图流（WS + REST 兜底） | ✅ |
| 截图 Canvas 边界框（三色） | ✅ |
| XPath 复制 + 添加到用例 | ✅ |
| Android 页面树管理 + 元素表格 | ✅ |
| Web 元素管理 + JSON 批量导入 | ✅ |
| API 端点管理 | ✅ |
| GroupTreePanel 接入（Web/API） | ✅ |
| 裸 client 收敛到 api.js | ✅ v6.0 |
| ElementManager 接入 GroupTreePanel | 📋 |
| useWebGroupTree + useApiGroupTree 合并 | 📋 |
| store.js + composables ElMessage 上移 | 📋 |
| ScreenshotView 589 行拆分 | 📋 |
| WebElementManager 1072 行拆分 | 📋 |

## 附录C：已知问题与改进项

| 编号 | 问题 | 严重度 | 记录日期 |
|:--:|------|:--:|:--:|
| IMP-01 | WebElementManager 1072 行超标（2x），需拆子组件 | 🔴 | 2026-07-27 |
| IMP-02 | PageElementsPanel 790 行 + ElementManager.css 703 行超标 | 🟠 | 2026-07-27 |
| IMP-03 | useWebGroupTree 和 useApiGroupTree 高度克隆（273 行 ×2），应合并为参数化 composable | 🟠 | 2026-07-27 |
| IMP-04 | store.js 和 3 个 composable 直接调用 ElMessage（BL 层引用 UI 层），应上移到 .vue | 🟠 | 2026-07-27 |
| IMP-05 | ElementManager.css 表格头 7 色渐变使用硬编码 hex，应迁移到 tokens.css | 🟡 | 2026-07-27 |
| IMP-06 | 50 处硬编码 hex 颜色分散在 7 个 .vue scoped CSS 中 | 🟡 | 2026-07-27 |
| IMP-07 | ElementManager 未使用 GroupTreePanel（自建 455 行树面板），与另两个 Manager 不一致 | 🟡 | 2026-07-27 |
