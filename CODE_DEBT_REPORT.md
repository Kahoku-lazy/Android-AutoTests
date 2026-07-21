# 技术债务报告 — V6 主题迁移 simplify 审查

> 生成日期：2026-07-22
> 审查范围：前端 8 模块 + 共享组件，60 个文件改动
> 审查方式：4 角度 × 8 模块 = 32 个 agent 并行分析

---

## 一、已修复项（本轮 /simplify 修复）

| 模块 | 修复内容 | 严重度 |
|------|---------|:--:|
| AI 助手 | 删除孤儿 `animal-theme.css`（与 tokens.css 色值冲突） | 🔴 |
| AI 助手 | `AgentDetail.vue` `cleanJson` 未定义 → `ReferenceError` 运行时崩溃 | 🔴 |
| AI 助手 | `EvaluatorTab.vue` `localStorage.getItem('token')` → `getToken()`（永远 `Bearer null`） | 🔴 |
| 元素定位 | `--glass-bg`/`--glass-border`/`--shadow` 未定义 → 5 组件面板玻璃态失效 | 🔴 |
| 元素定位 | 木板色残留 `rgba(139,115,85,*)` → V6 蓝调 | 🟠 |
| 元素定位 | 重复 `isConnected` guard 死代码 | 🟡 |
| 仪表盘 | StatsCard 蓝色顶条 `#C9B6F2` → `#BDE0FE`（错用紫色） | 🟠 |
| 仪表盘 | TaskResultPanel 20+ 处木板色 → V6 | 🟠 |
| 仪表盘 | TrendBarChart 木板色 chart 配置 → V6 | 🟠 |
| 用例管理 | 10 处 `#89CFF0` 硬编码无 CSS 变量包裹 → `var(--animal-primary-color, #89CFF0)` | 🟡 |
| 测试报告 | chart `setOption(notMerge:true)` → `setOption()`（数据更新不重建图表） | 🟡 |
| 全局 | 恢复 `@font-face` 字体拦截（防 3.4MB Noto Sans SC 下载） | 🟠 |
| 全局 | `<keep-alive>` 加 `:max="5"` 内存限制 | 🟠 |
| 全局 | `storage` 事件监听器泄漏修复（onMounted/onUnmounted） | 🟠 |
| 全局 | 删除 `animations.js` 中 3 个死函数（pageEnter/pageLeave/staggerIn/elasticHover） | 🟡 |
| 全局 | 提取 `shared/constants/module-colors.js` 消除 ModuleNavigator/StatsCard 重复 gradient | 🟢 |
| 全局 | `blur(20px)` → `var(--app-glass-blur)` | 🟢 |

---

## 二、跳过项 — 按优先级分组

### 🔴 P0：数据丢失与功能缺陷

| # | 模块 | 问题 | 影响 |
|---|------|------|------|
| 1 | **工作流** | 前端 10 种步骤类型 vs 后端 17 种 Python StepType — `perf_element_time`/`wait_toast`/`if_element_appear`/`if_element_disappear`/`loop_n`/`loop_elements` 在 `caseBridge.ts` 中被 `if (!STEP_TYPE_META[stepType]) continue` 静默丢弃 | 导入的测试用例会丢失 6 种步骤类型 |
| 2 | **执行引擎** | `index.vue` 无 `onUnmounted` — `queuePollTimer`（1.5s 轮询）、WebSocket 连接、`_saveTimer` 在页面离开后持续运行 | CPU/内存/网络泄漏 |
| 3 | **执行引擎** | `TaskDetail.vue` WebSocket handler 未在 unmount 时 `unregisterHandler`，消息持续推送到已销毁组件 | 后台 HTTP POST + 日志追加到死 ref |

> 注：P0-1 是工作流模块先于执行引擎开发的遗留问题，需同步 `models/step_types.py` StepType 枚举。P0-2/3 是 `index.vue(1186 行)` 和 `TaskDetail.vue(994 行)` 超行限的副产品。

### 🟠 P1：高重复代码（单文件改动多文件受益）

| # | 模块 | 问题 | 重复规模 |
|---|------|------|:--:|
| 4 | **用例管理** | 3 个编辑器（Api/Web/Storage）CSS 完全重复，24 条规则 | ~75 行 × 3 |
| 5 | **用例管理** | 4 个列表文件 toolbar/breadcrumb CSS 重复，12 条规则 | ~120 行 |
| 6 | **用例管理** | 编辑锁逻辑（`acquireLock`/`releaseLock`/`isLockedByOther`）在 3 个编辑器中完全重复 | ~135 行 |
| 7 | **用例管理** | `.btn-primary` CSS 在 7 个文件中独立定义，颜色格式不统一 | ~20 行 × 7 |
| 8 | **用例管理** | `breadcrumbPath` computed 在 4 个列表文件中重复（递归树遍历） | ~48 行 |
| 9 | **执行引擎** | 10 个函数在 `index.vue` 和 `TaskDetail.vue` 之间重复（`formatTime`/`ts`/`taskAddLog`/`restartTask`/`stopTask`/`removeTask`/`saveTask`/`stepTypeLabel`/`caseItems` 解析/`initTaskProgress`） | ~200 行 |
| 10 | **测试报告** | KPI 卡片 CSS + HTML 结构在 4 个文件中独立重复（`.kpi-row`/`.kpi-card`/`.kpi-accent` 等） | ~150 行 |
| 11 | **测试报告** | rate-cell CSS 在 3 个文件中重复（`.rate-cell`/`.progress-bar`/`.p-pass`/`.p-fail`） | ~90 行 |
| 12 | **测试报告** | `stepTypeLabel` 函数在 3 个文件中重复（test-runner/TaskDetail、report-generator 两个文件），`shared/constants/steps.js` 已有权威版本 | ~50 行 |
| 13 | **测试报告** | ECharts 生命周期样板代码在 2 个 chart 组件中完全重复（init/resize/dispose/zoomStart/watch/onUnmounted） | ~65 行 × 2 |
| 14 | **元素定位** | 2 个 panel 组件共享空状态动画逻辑（animejs watcher） | ~35 行 × 2 |

### 🟡 P2：架构规范违规

| # | 模块 | 问题 | 规范来源 |
|---|------|------|---------|
| 15 | **工作流** | `ImportCasesDialog.vue:7` 跨模块 import `@/modules/case-manager/api.js` | frontend.md §1 规则 2 |
| 16 | **执行引擎** | `index.vue:32-33` 跨模块 import `case-manager/api/apiTesting.js` + `webAutomation.js` | frontend.md §1 规则 2 |
| 17 | **AI 助手** | `ChatView.vue:240` 用原生 `fetch` + 手动 `Authorization` header 绕过 api-client 拦截器（无 401 自动刷新） | api-conventions.md |
| 18 | **AI 助手** | `EvaluatorTab.vue:182` 用 `localStorage.getItem('token')` 但项目用 `auth_accounts` pool（已修复此行，但文件内其他位置可能残留） | api-client.js |
| 19 | **执行引擎** | 5 个 API 端点直接 `client.post/get` 绕过 `api.js` 层 | backend.md 防火墙 #3 |
| 20 | **执行引擎** | `taskUtils.js:3-16` 用 localStorage 生成任务 ID 计数器，多标签会产生冲突 | 后端应分配 ID |
| 21 | **用例管理** | 4 个列表文件共用 `localStorage` key `"case-manager-view-mode"`，切换一个 tab 的视图模式会影响其他所有 tab | 应为 `case-manager-view-mode-${tabKey}` |

### 🟢 P3：效率优化

| # | 模块 | 问题 | 影响 |
|---|------|------|------|
| 22 | **工作流** | VueFlow 每次图变更触发全量 `refreshFromStore()`（O(N) 节点 + O(N*L) 边重建） | 拖一个节点，整个 canvas 重绘 |
| 23 | **工作流** | `TestCaseBlockly.vue` 每次 keystroke 触发 `pushToStore()` 全量树遍历 | 输入 "Hello" = 5 次遍历 |
| 24 | **工作流** | `toVueFlowEdges` 每条边 O(n) 线性扫描 | 20 节点 × 30 边 = 600 次比较 |
| 25 | **工作流** | `registerAutotestBlocks()` 每次挂载重新注册全局 Blockly 定义 | v-if 切换模式时重复注册 |
| 26 | **执行引擎** | `deep: true` watcher 监听整个 tasks 数组，WS 每条消息触发 | `stepStates` 变更也触发 |
| 27 | **执行引擎** | `filterAppTabs` computed 每条 WS 消息分配 5 个新对象 | GC 压力 |
| 28 | **执行引擎** | `stepStates` 每次 WS 消息做全量 `filter + sort`（O(n log n)） | 15 步=30 次分配/迭代 |
| 29 | **执行引擎** | `TaskDetail.vue` 无条件 3 秒 `setInterval` 保存，即使任务已完成 | ~20 HTTP/分钟 |
| 30 | **测试报告** | chart `watch` 用 `deep: true` 但父组件每次传新数组引用，浅监听已足够 | 无收益的 CPU 消耗 |
| 31 | **测试报告** | `chartRange`/`dateRange` watcher 无 debounce，快速点击触发多次 API | 废弃的网络请求 |
| 32 | **测试报告** | 图表 `ResizeObserver` 在 keep-alive 隐藏页面时继续触发 `echarts.resize()` | 不可见 canvas 重绘 |

---

## 三、根因分析

本轮 simplify 审查发现的核心模式：

1. **4-tab 模式导致 4 倍重复**：用例管理（UI/Web/API/Storage）、执行引擎（列表/详情）等模块中存在大量"复制粘贴后微调"的代码
2. **前端懒加载 + keep-alive 副作用**：WebSocket/定时器/ResizeObserver 在组件 deactivated 后继续运行
3. **跨模块 import 规则被绕过**：工作流和执行引擎直接 import 其他模块的内部 API
4. **前后端数据模型不同步**：工作流步骤类型 10 vs 17，静默数据丢失
5. **大量"温水煮青蛙"式技术债务**：重复的 CSS 类、重复的工具函数、重复的生命周期逻辑

---

## 四、建议修复路线

| 阶段 | 范围 | 预计工时 | 收益 |
|:--:|------|:--:|------|
| 1 | P0-2/3: 执行引擎 onUnmounted 清理 | 0.5d | 消除 WS/定时器泄漏 |
| 2 | P0-1: 工作流步骤类型同步 Python 17 种 | 1d | 消除静默数据丢失 |
| 3 | P1: 用例管理抽取共享编辑器/列表组件 | 3d | 消除 ~550 行重复 |
| 4 | P1: 执行引擎抽取 taskUtils.js 共享函数 | 1d | 消除 ~200 行重复 |
| 5 | P1: 测试报告抽取共享 KPI/rate-cell/chart composable | 2d | 消除 ~400 行重复 |
| 6 | P2: 修复跨模块 import 违规 | 0.5d | 解耦模块依赖 |
| 7 | P3: 效率优化（watcher/debounce/增量更新） | 2d | 减少无收益计算 |

> 注：P1 中的用例管理和执行引擎拆分同时解决文件超行限问题（index.vue 1186 行、TaskDetail.vue 994 行 vs 500 行硬限制）。
