# Frontend 代码约束 — Android-AutoTests

> 前端编码规范的**唯一真相源**，其他文件只做指针引用。
>
> 技术栈：Vue 3 + Vite + Element Plus，Doodle Craft 极简几何主题
> 设计令牌 → `frontend/DESIGN_SYSTEM.md` | CSS 工作流 → `frontend/CLAUDE.md`
> 模块边界 / API 格式 → `api-conventions.md` | 安全 → `security.md`

---

## 1. 命名规范

| 上下文 | 规范 | 示例 |
|--------|------|------|
| JS / Vue `<script>` | `camelCase` | `apiClient`, `getDevices()` |
| Vue 组件文件 | `PascalCase.vue` | `AgentDetail.vue`, `AppSidebar.vue` |
| Vue 模板 | `kebab-case` | `<device-pool>`, `<case-manager>` |
| CSS class | `kebab-case` | `.device-card`, `.test-result` |
| API URL | `kebab-case` | `/api/device-pool/` |
| JSON 字段 | `snake_case` | `{"test_case_id": 1}` |

---

## 2. 文件行数限制（阶梯式）

| 文件类型 | 上限 | 说明 |
|----------|:---:|------|
| `api.js` | **200** | 纯 HTTP 封装，应极薄 |
| composable | **300** | 单一职责，超限拆多个 composable |
| Vue 组件（总行数） | **400** | 模板 + 逻辑总计 |
| Vue `<template>` | **200** | 模板单独超限也触发拆分 |

**阶梯处理**：

| 达到上限 | ⚠️ 关注，下个 PR 评估 |
| 超过 1.5 倍 | 🟠 禁止新增代码，必须附带拆分计划 |
| 超过 2 倍 | 🔴 只允许拆分重构，禁止堆代码 |

> **自查**：`find frontend/src -name "*.vue" -o -name "*.js" | xargs wc -l | sort -rn | head -20`

---

## 3. 架构红线

1. **按业务域拆分** — 新代码放 `modules/{domain}/`，删一个模块 = 删一个目录
2. **模块自治** — 模块间只通过 `router.push`、`shared/components/`、`event-bus` 交互，不互相 import 业务逻辑
3. **调用链单向** — `components/ → composables/ → api.js`，上层不反向引用下层
4. **三层职责**：
   - `components/` — 只渲染 + emit，❌ 禁止直接调 axios/apiClient
   - `composables/` — 状态 + 逻辑 + API，❌ 禁止操作 DOM
   - `api.js` — 纯 HTTP，❌ 禁止处理业务状态

---

## 4. 组件拆分信号

出现以下**任一信号**就该拆：

| 信号 | 阈值 |
|------|------|
| ref / reactive | > 6 个 |
| 模板行数 | > 200 行 |
| 文件总行数 | > 400 行 |

---

## 5. 数据加载三态规程

每个有数据请求的页面/组件**必须处理三种状态**：

```
组件挂载 → loading = true
  ├── 请求成功 + 数据非空 → loading = false, 渲染内容
  ├── 请求成功 + 数据为空 → loading = false, <EmptyState />
  └── 请求失败           → loading = false, error = "...", <ErrorState />
```

**模板骨架**（复制此结构）：
```vue
<ErrorState v-if="error" :message="error" @retry="fetchData" />
<template v-else>
  <div v-loading="loading">
    <EmptyState v-if="!list.length" icon="📋" text="暂无数据" />
    <!-- 正常内容 -->
  </div>
</template>
```

**script 标准写法**：
```javascript
const list = ref([])
const loading = ref(false)
const error = ref("")

async function fetchData() {
  loading.value = true        // 请求前设 true
  try {
    const { data } = await api.getXxx()
    if (data.ok) {
      list.value = data.items
      error.value = ""        // 成功后清除（不是请求前！）
    }
  } catch (e) {
    error.value = "加载失败，请检查网络连接"
  } finally {
    loading.value = false
  }
}
```

**禁止**：
- ❌ `try { await api.deleteX(id) } catch (_) {}` — 写操作静默吞错
- ❌ 只有 loading 没有 error — 请求失败时页面永远转圈
- ❌ `error.value = ""` 放在 try 第一行 — retry 时内容区闪白
- ❌ `@retry` 用内联箭头函数 — 提取为 `@retry="fetchData"`
- ❌ 每个 `<section>` 写 `v-if="!error"` — 用一个 `<template v-else>` 包裹全部内容

---

## 6. CSS 架构层级协议

三层结构，**不可跨层覆盖**：

| 层级 | 文件 | 允许 | 禁止 |
|:--:|------|------|------|
| L1 令牌 | `shared/styles/tokens.css` | 定义 CSS 变量（`--app-*`、`--el-*`） | 写选择器、写组件样式 |
| L2 全局 | `src/style.css` | 全局布局骨架 + Element Plus 全局覆盖 | 模块专属样式、硬编码色值 |
| L3 模块 | `modules/{x}/*.vue <style scoped>` | 本模块布局微调、动画、间距 | **重定义 L2 同名类** |

**模块与 L2 的正确交互**：
- 改 `.doc-body` padding → CSS 变量：`style="--doc-padding: 12px"`
- 改 `.doc-section` 边框色 → 内联：`style="border-color: var(--c-xxx)"`
- **禁止**在 scoped 中写 `.doc-body { padding: ... }` 与 L2 竞争优先级

**翻车记录**（曾因此协议违反导致的 Bug）：
- `info-card` 残留 `overflow:hidden` → 报告页无法纵向滚动
- `el-tabs__content` 默认 `overflow:hidden` + 中间层 `overflow:hidden` → 三层裁剪
- `.doc-body` 设 `max-width: 1600px` → 大屏两侧 ~480px 空白

---

## 7. 样式约束

1. **颜色/圆角/阴影/字体从 `tokens.css` 取** — ❌ scoped 中硬编码色值
2. **覆盖 Element Plus 用 `:deep()` + `--el-*` 变量** — ❌ 封装薄 wrapper
3. 当前主题 → `frontend/DESIGN_SYSTEM.md`
4. **改样式只改 CSS** — 不动 props/emits/API/路由/动画
5. **布局改动后验证滚动** — flex/grid/overflow 改动在浏览器确认页面可纵向滚动

---

## 8. 状态管理

> 📋 什么时候用 ref / composable / Pinia？→ `frontend/CLAUDE.md` 状态管理决策树

**升级路径**：`ref` → `composable` → Pinia（只在 workflow 模块允许 Blockly/VueFlow store）

**禁止**：
- ❌ `shared/composables/` 之外创建 Pinia store
- ❌ 新模块默认用 Pinia — 必须先从 ref 开始

---

## 9. 异常处理

Vue 无 ErrorBoundary。按层级分工防止白屏：

| 层级 | 机制 | 规则 |
|------|------|------|
| 全局 | `app.config.errorHandler` | 捕获未处理异常，不白屏 |
| 页面 | ErrorState 组件 | 网络请求失败 → ErrorState + 重试 |
| 组件 | `onErrorCaptured` | 子组件异常 → 父组件捕获，降级 UI |

**禁止**：
- ❌ `<script setup>` 顶层抛异常（setup 阶段无法被 errorHandler 捕获）
- ❌ `await` 不包 try/catch
- ❌ 用 `v-if` 隐藏错误不上报

---

## 10. 共享组件使用规则

> 📋 什么场景用哪个共享组件？→ `frontend/CLAUDE.md` 共享组件速查

**禁止**：
- ❌ 手写 `<div class="empty-state">暂无数据</div>` — 用 `<EmptyState>`
- ❌ 手写 `<div v-if="error" class="xxx-error">{{ error }}</div>` — 用 `<ErrorState>`

**自建同类组件的条件**（全部满足才可自建）：
1. 共享组件确实不满足交互需求（拖拽排序、右键菜单、内联编辑等）
2. PR 描述中说明为何不用共享组件
3. 优先考虑增强共享组件而非另起炉灶

---

## 11. 模块结构一致性

每个模块目录必须包含（占位页面除外）：

```
modules/{name}/
├── index.vue       ← 页面容器
├── api.js          ← HTTP 封装（即使只导出 1 个函数）
├── routes.js       ← 路由定义
├── components/     ← 子组件（即使只有 1 个）
└── composables/    ← 状态/逻辑（即使只有 1 个）
```

**禁止**：
- ❌ 模块目录放独立 `.css` — 样式在 `<style scoped>` 或 `tokens.css` 中
- ❌ 模块目录放 `store.js` / `stores/` — Pinia store 仅 workflow 模块
- ❌ `index.vue` 的 `<script setup>` 中 > 20 行 fetch/业务逻辑 — 抽到 composable

---

## 12. Element Plus 陷阱

**el-cascader**: `emitPath` 默认 `true` → v-model 绑定路径数组 `[1,5]`，后端期望单个 ID。必须显式 `emitPath: false`。

使用不熟悉的复杂组件（el-cascader/el-tree-select/el-transfer）时：查文档确认默认值 → 确认 v-model 类型与后端一致 → `grep` 已知陷阱 → curl 往返验证。

---

## 13. Vite Proxy

```
/api  /ws  → :8765 (Django)
/agentscope → :8000 (AgentScope)
```

WebSocket URL 必须走 Vite 代理（`wsUrl('/ws/...')`），禁止直连 `:8765`。

---

## 14. 页面空白排查

全局 CSS 继承是最隐蔽的坑 — scoped 内正常但 `style.css` 覆盖了关键属性。看 DevTools Computed 面板的**最终值和来源文件**。尤其 `flex-direction` 被全局继承为 column 时。

---

## 15. 质量门禁

```bash
# 编译
cd frontend && npx vite build --mode development 2>&1 | tail -10

# 样式自查 — 禁止组件内硬编码色值
grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" \
  frontend/src/modules/ --include="*.vue" | grep -v "tokens\|style.css"

# el-cascader emitPath 陷阱
grep -rn "el-cascader" frontend/src/modules/ | grep -v "emitPath"
```

### 浏览器验证（改以下文件必须）

| 改动 | 验证 |
|------|------|
| router/routes | 点侧边栏每个菜单 → 确认加载 |
| api-client | 登录 → 刷新 → 不跳回登录页 |
| ChatView/SSE | 发一条消息 → 流式回复正常 |
| LoginView | 登录 → 跳转 dashboard |
| AppSidebar | 菜单项完整 |

---

## 16. 自评

1. 10 分钟能加一个 CRUD 页面？→ 模式一致
2. 改一个颜色全局生效？→ 令牌驱动，无硬编码色值
3. 新页面含 loading / empty / error 三态？→ 数据加载契约完整
4. 删一个模块不影响其他？→ 无跨模块网状 import
5. 没有新建 Pinia store / 独立 .css / 手写空状态？→ 共享组件优先
