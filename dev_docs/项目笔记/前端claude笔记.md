# CLAUDE.md — 前端

> 本文定位：**行为决策** — 什么时候做什么、选什么方案。每次收到前端任务第一个读。

## 文档速查

| 我要…… | 读这个 |
|------|------|
| 判断改动的边界和步骤 | 本文 → 0️⃣ 改前四步 |
| 选状态方案（ref / composable / Pinia） | 本文 → 状态管理决策树 |
| 找现成的共享组件 | 本文 → 共享组件速查 |
| 查具体实现约束和红线 | `frontend/CLAUDE.md`（AI 约束摘要）+ `../.claude/rules/frontend.md` |
| 登录/表单/图标/重构取舍 | 本文 → 编码行为规范（含登录暂缓触发表） |
| 改完 .vue 门禁自检 | `.claude/skills/vue-frontend-check/` |
| 复制页面/组件代码骨架 | `frontend/DESIGN_SYSTEM.md` |
| 查前后端字段名对照 | `../dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` |

---

## 编码行为规范（默认取舍）

> 源自 LoginView 重构验证过的原则。改 Vue / composable / 图标 / 表单认证时默认遵守。  
> 口诀：**展示不碰网，流程不做校验，类型跟着实现走，图标进工厂，共享等第二人，重构先问值不值。**

### 1. 职责边界

| 层 | 只做 | 不做 |
|----|------|------|
| `.vue` 展示组件 | 渲染、v-model/emit、testid | API、token、路由跳转、复杂校验编排 |
| 页面编排（`*.logic.ts`） | 组合 composable、提交前校验、切视图清表单 | 直接 `axios`/`fetch` |
| 流程 composable（如 `useAuthFlow`） | 调 API → 写副作用 → 跳转 | 表单字段校验、弹校验 toast |
| 校验 composable（如 `useLoginForm`） | 产出 `errors` / `canSubmit` | 发请求 |

**硬规则**：函数名暗示「认证 / 请求」的，禁止顺手塞「表单是否可提交」逻辑。校验失败提示放在**调用方**（`handleLogin` / `handleRegister`）。

```text
✅ handleLogin: if (!canLogin) { ElMessage.warning(...); return } → authenticate(...)
✅ authenticate: 只处理网络与登录态
❌ authenticate({ canSubmit, errors }) 内部再判校验
```

### 2. 类型与实现必须同改

- 改函数参数时：**公开 interface / 返回类型签名与实现参数表一次改齐**。
- 禁止「实现已收参、导出类型却没有」这类文档性 bug。
- 调用方、单元测试与签名同步更新；职责上移时，对应用例跟着上移（校验测编排层，不测 API 层）。

### 3. 图标与共享资源

- 新图标在 `frontend/src/shared/icons/index.ts` 用 **`makeIcon(...)` 加一条导出**。
- **禁止**为单个图标新建 `IconXxx.vue`（除非工厂无法表达）。
- 模板统一：`<IconXxx :size="18" class="form-icon" />`。
- 抽到 `@/shared/components`：**第二个真实消费方出现再抽**；只有一处用时留在模块内。

### 4. 命名

| 场景 | ✅ | ❌ |
|------|----|----|
| 包装后再调用的内部函数 | `baseSwitchMode` / `rawSwitchMode` | `_switchMode`（易被当成未使用） |
| 仅编排用的 handler | `handleLogin` / `handleRegister` | 强行动态统一牺牲类型 |
| 校验失败文案 | `firstError \|\| '请完善表单'` | 假定 errors 非空直接 warning |

### 5. 重构克制（默认不做）

除非有明确第二场景或缺陷驱动，否则拒绝：

- `<component :is>` 合并 props/emits 不同的卡片
- 整表改 `reactive(formData)` 连锁改 5+ 文件
- 首屏关键图 `loading="lazy"`（伤 LCP）
- 仅 1～2 处路径硬编码就抽路由常量
- 工作正常的 CSS `@import` 大治理（需 E2E，单独排期）
- 无行为变化的 `computed` 间接层

**允许的低成本改进**（样式靠 class、无行为变化时可顺手做）：语义标签 `header`/`main`/`footer`、`aria-label`、装饰图 `alt=""`、解构分组注释。

### 6. 展示组件目录（如 `views/components`）

- 子组件已是纯展示 → **不必为「配套重构」而改**。
- 仅在这些情况改：换图标、改 props/emits 契约、修 UI bug、补无障碍。
- 单处使用的浮层/卡片不提前抽 shared。

### 7. 关单前（认证/表单相关至少覆盖）

```text
[ ] 公开类型与实现一致
[ ] 校验在调用方；API composable 无表单校验
[ ] 新增图标走 makeIcon
[ ] 相关单测已随职责迁移
[ ] data-testid 未无故改名
[ ] 真实页面点过关键路径（构建通过 ≠ 完成）
```

### 8. 登录相关暂缓项（触发表）

> LoginView Phase 1–2 已落地。下列项**默认不做**；仅当触发条件满足时再开改。

| 改动 | 暂缓理由 | 触发条件 |
|------|----------|----------|
| `LoginErrorOverlay` → `@/shared/components/MessageOverlay` | 仅 1 处消费 | 第二个页面需要全局消息弹窗 |
| CSS `@import` 治理（`login-card.css` / `auth-form-card.css`） | 现网正常；动构建顺序需 E2E | 出现样式覆盖 bug，或引入 CSS Modules |
| `/dashboard` 抽成路由常量 | 仅 2 处硬编码，收益低 | 出现第 3 处相同路径硬编码 |
| `useLoginForm` 位置参数 → 对象参数 | 仅 1 处调用方 | 第二个模块要复用 `useLoginForm` |
| `LoginViewState` 去掉对外暴露的 `accountList` | 影响面小 | 做 composable 接口清理时一并处理 |

---

## 0️⃣ 改前准备（动手之前必走）

收到"改 UI"指令后，不直接写代码。先走完下面四步，再跳转到 ①②③ 执行。

### 第一步：理解需求，确认修改范围

```
"改 UI" →
  ├── 需求明确（"把设备列表的 ONLINE 标签从红色改绿色"）→ 继续
  └── 需求模糊（"优化一下设备页"）→ 列 3-5 个具体理解让用户选，不默默挑一种执行
```

不假设。不隐藏困惑。不确定时主动问：改哪个页面？改什么元素？期望的效果是什么？

### 第二步：定位当前位置

```bash
# 1. 列出模块所有 .vue
ls frontend/src/modules/{domain}/components/

# 2. 逐个 Read 三个块
#    <template>   → DOM 结构 + 数据绑定 + class 名
#    <script setup> → props / emits / ref / computed / 调了哪些 api.js
#    <style scoped> → 用了哪些 CSS 变量 + 类名列表

# 3. 提取模板中全部 class（防止漏 inner class）
grep -oP 'class="[^"]*"' target.vue | sort -u
```

**为什么要读完三个块才动手？** 反面教材：只看了 `<style>` 就开改，删了 340 行旧 CSS。凭印象写新 CSS 只覆盖主类名，漏了 `.fail-card`、`.issue-row`、`.task-block` 等 12+ 个 inner class，用户报一个补一个，5 轮才修完。

### 第三步：查约束规则

**通用约束（不管改哪都要守）：**

| 查什么 | 去哪看 | 守什么 |
|--------|--------|--------|
| 架构红线 | `../.claude/rules/frontend.md` | 调用链单向、三层职责、文件上限 500 行 |
| 设计系统 | `frontend/DESIGN_SYSTEM.md` | 改颜色→§1 色板+§1.3状态色 / 改组件→§3组件模板 / 改Element Plus→§2原子层 / 改布局→§4页面层 / 嵌套+表格+表单→§5工程约束 |
| 命名规范 | `../.claude/rules/conventions.md` | PascalCase.vue / kebab-case 模板 / camelCase JS / snake_case JSON |

**模块专属约束（改哪个模块，查哪条约束）：**

| 模块 | 特殊约束 | 踩坑后果 |
|------|---------|---------|
| `element-locator` | WS 截图流 2fps 不能阻塞主线程；dump 结果 `_idx`/`_xpaths`/`_testpoint` 前缀字段不能用错 | 截图流卡顿或断连 |
| `case-manager` | 步骤 JSON 结构不能破坏；`steps_data` 序列化字段名与 StepType 枚举对齐 | 用例保存后执行失败 |
| `ai-assistant` | SSE 事件类型决定渲染时机；`MessageBubble`/`ToolCallCard`/`ThinkingBlock` 各有独立折叠规则 | AI 对话 UI 错乱 |
| `test-runner` | WS 6 种事件 type 一个不能漏；`runProgress` 结构决定进度条正确性 | 进度不更新或页面空白 |
| `report-generator` | 报告下载是 FileResponse 非 JSON，必须用 `fetch().text()` 而非 `api()` | 报告内容乱码 |
| `device-pool` | 设备状态只有 3 种（ONLINE/BUSY/OFFLINE），无 DISCONNECTED | 状态标签渲染错误 |
| `dashboard` | 纯聚合只读，**禁止写操作** | 违反模块边界 |
| `workflow` | Blockly/VueFlow 内部状态不能外部直接篡改 | 可视化编排数据丢失 |

### 第四步：判边界 → 跳转执行

```
改动涉及什么？
  ├── 只改颜色/间距/布局/动画/组件内部状态     → 跳转到 ①
  ├── 数据显示变了，需要新字段或改 API 调用      → 跳转到 ②
  ├── 改了 AI 对话的气泡/ToolCard/思考块/输入框  → 跳转到 ③
  └── 跨了多个边界                              → 逐个按 ①②③ 顺序执行
```

---

### 新模块检查清单

新建 `modules/{name}/` 时，逐项打勾：

```
[ ] 5 个文件齐全: index.vue + api.js + routes.js + components/ + composables/
[ ] router.js 已注册（1 行 import + 1 行 spread）
[ ] AppSidebar.vue 已注册菜单项
[ ] index.vue 含 ErrorState + EmptyState + v-loading 三态
[ ] WorkbenchHeader 的 icon-gradient 使用模块色 var(--c-xxx)
[ ] 无独立 .css 文件、无 Pinia store（workflow 除外）
```

---

## ① UI 状态管理（纯 Vue，零外部依赖）

改这部分不影响任何后端模块，改完构建通过即可上线。

### 修改铁律

1. **先出原型，再写代码** — 改任何模块前先出 3 个 HTML 概念原型
2. **只改 CSS，不改逻辑** — 不碰 props/emits/API/路由/动画

### CSS 替换标准流程

改一个文件的 `<style>` 块时：
```bash
# 1. 提取模板中所有 class（0️⃣ 第二步已完成）
grep -oP 'class="[^"]*"' target.vue | sort -u > /tmp/classes.txt

# 2. 逐个确认新 CSS 里每个 class 都有规则
# 3. 再删旧 CSS、写新 CSS
# 4. 构建 + grep 残留
```

### 布局修改 Debug 流程

改完 CSS 后：
1. 在浏览器打开实际页面（非原型 HTML）
2. 纵向缩小窗口 → 检查页面是否可滚动
3. 不能滚动 → DevTools 逐层查 `overflow` 属性，找到所有 `hidden` 的容器
4. 表格区必须 `flex: 1 1 0; min-height: 0; overflow-y: auto`（Flexbox 默认 min-height:auto 阻止滚动）
5. 外层卡片容器不能有 `overflow:hidden`

> 反面教材：改报告生成器 CSS → 构建通过 → 以为完成 → 实际页面不可滚动。根因：`info-card` 残留 `overflow:hidden` + `el-tabs__content` 的 `overflow:hidden` 三层裁剪。

### 状态管理边界

| 用 `ref` | 用 Pinia store | 用 localStorage |
|----------|---------------|-----------------|
| 组件内状态 | 跨组件共享（设备/用例/Agent） | 持久化偏好（视图模式/主题） |

优先 `ref` → 不够用 composable → 还不够才 Pinia。

### ① 改动验证

```
改 CSS/布局  → 构建 → 浏览器 → 缩小窗口确认可滚动
改组件状态   → 确认 ref/reactive < 6 个（超了该拆子组件）
改 localStorage → 检查 key 格式是否统一
```

---

## 状态管理决策树

改状态时按此顺序选择，**不可跳级**：

| 优先级 | 方案 | 适用场景 | 示例 |
|:--:|------|------|------|
| 1 | `ref` / `reactive` | 组件内状态，不跨组件共享 | 表单输入、弹窗显隐、筛选条件 |
| 2 | composable | 同模块内多组件共享，或有复用价值 | `useElementTree()`、`useTaskWebSocket()` |
| 3 | Pinia store | 跨模块共享 + 需持久化 + 复杂状态机 | 设备连接状态、工作流编辑器画布 |

**升级信号**：ref 被 3+ emit 传递 → composable；composable 被 2+ 模块 import → shared/；composable 有 5+ 依赖 ref → Pinia。
**禁止**：新模块默认用 Pinia（先 ref 起步）；在 shared/ 之外新建 Pinia store（workflow 特例）。

## 共享组件速查

以下场景**必须用共享组件，禁止自建**：

| 场景 | 组件 | 场景 | 组件 |
|------|------|------|------|
| 错误+重试 | `ErrorState` | 空数据 | `EmptyState` |
| 卡片布局 | `AppCard` | 数据表格 | `AppTable` |
| Tab 切换 | `AppTabs` | 树形面板 | `GroupTreePanel` |
| KPI 统计 | `KpiCard` | 筛选标签 | `FilterTabs` |
| 骨架屏 | `SkeletonCard` | 确认按钮 | `ConfirmButton` |

> 📋 详细约束和禁止项 → `../.claude/rules/frontend.md` §共享组件使用规则

---

## ② Django 交互协议（HTTP + WebSocket）

改这部分需要确认 API 字段名一致，对照 `VUE_API_CONTRACT.md` 校验。

### HTTP 调用链（经 DRF）

```
组件 emit → composable 调 api.js/api/*.ts → djangoClient → /api/...（Vite 代理）→ Django DRF → {status, data|message} → 更新 ref
```

**铁律：**
1. 组件不直接调 axios/fetch，必须走模块 `api`。
2. 业务 HTTP 经统一客户端访问 **DRF**，禁止旁路直连后端端口。
3. 逻辑层（composable + api）的路径/方法/字段须与后端 `urls` + Serializer / `VUE_API_CONTRACT` 一致。

### JSON 字段转换

| 层 | 规范 | 示例 |
|----|------|------|
| JS 变量 | `camelCase` | `testDefinitions`, `lastDump` |
| HTTP 请求/响应 JSON | `snake_case` | `{"page_id": 1, "element_count": 5}` |

api.js 封装层处理转换。

### 响应格式

```json
{"status": true, "data": {...}}   // 成功
{"status": false, "message": "..."}  // 失败
```

**禁止** `try { await api.deleteX(id) } catch (_) {}` — 写操作静默吞错。

### WebSocket

- **URL 构建**：必须走 Vite 代理 `wsUrl('/ws/...')`，禁止直连 `:8765`
- **截图流** (`/ws/screenshot`)：后端每 500ms 推一帧 base64 → canvas 渲染
- **执行进度** (`/ws/test-run/{id}`)：6 种事件 — `log` / `case_started` / `step_result` / `case_finished` / `run_finished` / `device_error`，每个 type 在 `handleTestMessage` switch 中都要有处理

### ② 改动验证

| 改动类型 | 验证方式 |
|----------|---------|
| 新增/修改 API 调用 | `curl` 往返验证 → 确认 `{ok, data}` 结构 |
| 改 api.js | 登录 → 刷新 → 不跳回登录页（401 拦截器正常） |
| 改 WS URL | DevTools Network → WS → 状态码 101，持续收到帧 |
| 改报告下载 | 确认用 `fetch().text()` 而非 `api()`（FileResponse 非 JSON） |
| 改 router/routes | 点侧边栏每个菜单 → 确认加载 |
| 改 LoginView | 登录 → 跳转 dashboard |

### 常见断裂点

| 问题 | 前端表现 | 原因 |
|------|---------|------|
| 后端改了 JSON 字段名 | 页面空白，无报错 | `data.xxx` 为 undefined |
| `api()` 拿到非 JSON | 解析异常 | 后端返回了 HTML/纯文本 |
| WS type 不匹配 | 日志不更新 | switch 未命中 |
| 请求体字段名不一致 | `{ok:false, error:"..."}` | snake_case vs camelCase |

---

## ③ AgentScope 交互协议（SSE 流式）

AgentScope 在 Django 进程内运行，前端 SSE 直连 Django（不经独立 :8000 服务）。

### SSE 调用链

```
用户发消息 → POST /api/ai/conversations/{id}/chat/stream (JWT) → Django → AgentScope (进程内) → SSE 流 → 前端渲染
```

### SSE 事件类型 → 前端渲染映射

| 事件 | 前端渲染 |
|------|---------|
| `REPLY_START` | 消息气泡出现，开始新回复 |
| `TEXT_BLOCK_DELTA` | 追加文本到消息气泡（逐字打字效果） |
| `THINKING_BLOCK_START` | 渲染 ThinkingBlock（可折叠推理过程） |
| `THINKING_BLOCK_DELTA` | 追加推理文本 |
| `THINKING_BLOCK_END` | 折叠 ThinkingBlock |
| `TOOL_CALL_START` | 渲染 ToolCallCard（loading 态） |
| `TOOL_CALL_DELTA` | 追加工具参数 JSON |
| `TOOL_RESULT_START/DELTA/END` | 更新 ToolCallCard（显示结果摘要） |
| `HINT_BLOCK` | 渲染 SOP 状态卡片 / 任务卡片 |
| `REQUIRE_USER_CONFIRM` | 显示 HITL 确认弹窗 |
| `REPLY_END` | 消息完成 → 调 `save-message` 持久化 |
| `error` | 显示错误提示，允许重试 |

### 连接管理

| 场景 | 处理 |
|------|------|
| 断线重连 | 自动重试，最多 3 次，间隔递增（1s/2s/4s） |
| 用户点"停止" | 关闭 SSE → 保留已生成内容 |
| AI 不可用 | 自动降级 Django 阻塞模式 `POST /api/ai/chat/sync` |

### 子组件折叠规则

| 组件 | 输入/参数 | 输出/结果 |
|------|:--:|:--:|
| ThinkingBlock | — | 默认折叠，用户手动展开 |
| ToolCallCard | 默认折叠 | 默认展开 |

### ③ 改动验证

| 改动类型 | 验证方式 |
|----------|---------|
| 改 SSE 事件处理 | 发一条消息 → 流式回复正常 → 思考块可折叠 → ToolCard 有结果 |
| 改停止生成 | 发送消息 → 中途点停止 → 已生成内容保留 |
| 改消息渲染 | 发多条消息 → 确认 Markdown 渲染正确（代码块/表格/列表） |

---

## ④ 数据加载标准模式

> 📋 完整骨架代码（复制即用）→ `DESIGN_SYSTEM.md` §4.7

### 关键规则（踩坑记录）

| # | ✅ 正确 | ❌ 错误 |
|---|------|------|
| 1 | `@retry="fetchData"`（命名函数） | `@retry="() => { ... }"`（内联箭头每次渲染重建） |
| 2 | `error.value = ''` 放 `data.status` 内（成功后清除） | `error.value = ''` 放 try 第一行（retry 时闪白） |
| 3 | `<template v-else>` 包裹全部内容 | 每个 `<section>` 各自写 `v-if="!error"` |
| 4 | 一个页面一个 ErrorState | 每个 tab slot 各放一个 |
| 5 | `finally { loading = false }` | 只在 try 关 loading（catch 永远转圈） |

### ④ 改动验证

| 改了什么 | 验证方式 |
|---------|---------|
| 新增 fetch 页面 | 断网 → 刷新 → ErrorState + 重试 → 恢复 |
| 新增列表组件 | 空 DB → EmptyState（非空白）；有数据 → 正常 |

---

## 最终验证（所有改动必走）

```
[ ] 构建通过  cd frontend && npx vite build --mode development
[ ] 浏览器验证实际页面（非原型 HTML）
[ ] grep 残留色值   grep -rnP "color:\s*#[0-9a-fA-F]" src/modules/ --include="*.vue" | grep -v tokens
[ ] grep 残留旧类名（如果有删旧 CSS）
[ ] 文件未超上限  find src/modules/ -name "*.vue" | xargs wc -l | sort -rn | head -5
[ ] 自评 3 问：
      1. 删这个模块，其他模块不受影响？
      2. 改这个颜色，全局生效（从令牌取）？
      3. diff 里每一行都能追溯到用户的需求？
```
