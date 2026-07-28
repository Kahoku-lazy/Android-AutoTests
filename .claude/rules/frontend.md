# Frontend Rules — Android-AutoTests

> AI 前端开发的行为约束。本文是前端架构约束的**唯一真相源**，其他文件只做指针引用。
>
> 技术栈：Vue 3 + Vite + Element Plus，8 模块，Doodle Craft 极简几何主题
> 设计令牌 → `frontend/DESIGN_SYSTEM.md` | CSS 工作流 → `frontend/CLAUDE.md`
> 命名规范/行数上限 → `.claude/rules/conventions.md` | API 格式/模块边界 → `.claude/rules/api-conventions.md`

---

## 架构红线

1. **按业务域拆分** — 新代码放 `modules/{domain}/`，删一个模块 = 删一个目录
2. **模块自治** — 模块间只通过 `router.push`、`shared/components/`、`event-bus` 交互，不互相 import 业务逻辑
3. **调用链单向** — `components/ → composables/ → api.js`，上层不反向引用下层
4. **三层职责**：
   - `components/` — 只渲染 + emit，❌ 禁止直接调 axios/apiClient
   - `composables/` — 状态 + 逻辑 + API，❌ 禁止操作 DOM
   - `api.js` — 纯 HTTP，❌ 禁止处理业务状态

## 代码约束

### 组件拆分信号（出现任一就该拆）
| 信号 | 阈值 |
|------|------|
| ref/reactive | > 6 个 |
| 模板行数 | > 150 行 |
| 文件总行数 | > 300 行（硬上限 500） |

### 命名
文件 `PascalCase.vue`，模板 `kebab-case`，JS `camelCase`，JSON `snake_case`

### 数据
- ❌ 组件同时从 props 和 onMounted 请求同一份数据
- ❌ 硬编码假数据 `ref([{ id: 1, name: '测试' }])`
- ❌ 写操作静默吞错 `try { await deleteX(id) } catch (_) {}`
- 状态管理：能用 `ref` 不用 Pinia，能用 composable 不用 event bus

## 样式约束

1. **颜色/圆角/阴影/字体从 `tokens.css` 取** — ❌ 组件 scoped 中硬编码色值
2. **覆盖 Element Plus 用 `:deep()` + `--el-*` 变量** — ❌ 禁止封装薄 wrapper
3. 当前平台主题 → `frontend/DESIGN_SYSTEM.md`
4. **修改样式只改 CSS** — 不碰 props/emits/API/路由/动画逻辑
5. **布局改动后验证滚动** — 涉及 flex/grid/overflow 时，浏览器中确认页面可纵向滚动

## 状态管理

> 📋 什么时候用 ref / composable / Pinia？→ `frontend/CLAUDE.md` 状态管理决策树

**禁止**：
- ❌ 在 `shared/composables/` 之外创建 Pinia store（workflow 模块 3 个 store 特例除外）
- ❌ 新模块默认用 Pinia — 必须先从 ref 开始，按需升级

## CSS 架构层级协议

三层结构，**不可跨层覆盖**：

| 层级 | 文件 | 允许 | 禁止 |
|:--:|------|------|------|
| L1 令牌 | `shared/styles/tokens.css` | 定义 CSS 变量（`--app-*`、`--el-*`） | 写选择器、写组件样式 |
| L2 全局 | `src/style.css` | 全局布局骨架（`.doc-page`、`.doc-body`、`.doc-section`）+ Element Plus 全局覆盖 | 模块专属样式、硬编码色值 |
| L3 模块 | `modules/{x}/*.vue <style scoped>` | 本模块的布局微调、特有动画、组件间距 | **重定义 L2 同名类**（如在 scoped 中写 `.doc-body { ... }`） |

**模块与 L2 的正确交互方式**：
- 想改 `.doc-body` 的 padding？→ 用 CSS 变量覆盖，如 `style="--doc-padding: 12px"`（先在 tokens 定义变量）
- 想改 `.doc-section` 的边框色？→ 内联覆盖：`style="border-color: var(--c-xxx)"`
- **禁止**在 scoped 中写 `.doc-body { padding: ... }` 与 L2 同名选择器竞争优先级

**翻车记录**（曾因违反此协议导致的 Bug）：
- `info-card` 残留 `overflow:hidden` → 报告页无法纵向滚动
- `el-tabs__content` 默认 `overflow:hidden` + 中间层 `overflow:hidden` → 三层裁剪
- 全局 `.doc-body` 设 `max-width: 1600px` → 大屏（2560px+）两侧 ~480px 空白

## 数据加载三态规程

每个有数据请求的页面/组件**必须处理三种状态，缺一不可**：

```
组件挂载 → loading = true
  ├── 请求成功 + 数据非空 → loading = false, 渲染内容
  ├── 请求成功 + 数据为空 → loading = false, <EmptyState />
  └── 请求失败           → loading = false, error = "...", <ErrorState />
```

**模板标准写法**（复制此骨架）：
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
  loading.value = true  // 请求前设 true
  try {
    const { data } = await api.getXxx()
    if (data.ok) {
      list.value = data.items
      error.value = ""  // 成功后清除（不是请求前！避免 retry 时页面闪白）
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
- ❌ 只有 `empty-text` 属性没有 `<EmptyState>` 组件 — 首次加载空列表应显示引导操作
- ❌ `error.value = ""` 放在 try 第一行 — 会导致 retry 时内容区闪白再出现
- ❌ `@retry` 用内联箭头函数 — 提取为 `@retry="fetchData"` 命名函数
- ❌ 每个 `<section>` 写 `v-if="!error"` — 用一个 `<template v-else>` 包裹全部内容

## 异常处理规则

Vue 无 ErrorBoundary。按层级分工防止白屏：

| 层级 | 机制 | 规则 |
|------|------|------|
| 全局 | `app.config.errorHandler`（main.js 已配置） | 捕获未处理异常，输出 console，不白屏 |
| 页面 | ErrorState 组件 | 网络请求失败 → ErrorState + 重试（见数据加载三态规程） |
| 组件 | `onErrorCaptured` | 子组件渲染异常 → 父组件捕获，显示降级 UI |

**禁止**：
- ❌ `<script setup>` 顶层抛异常（setup 阶段异常无法被 errorHandler 捕获）
- ❌ `await` 不包 try/catch — 异步异常必须显式处理
- ❌ 用 `v-if` 隐藏错误不上报 — 隐藏的错误在生产环境无法追踪

## 共享组件使用规则

> 📋 什么场景用哪个共享组件？→ `frontend/CLAUDE.md` 共享组件速查

**自建同类组件的条件**（全部满足才可自建）：
1. 共享组件确实不满足交互需求（如需要拖拽排序、右键菜单、内联编辑）
2. 在 PR 描述中说明为何不用共享组件
3. 优先考虑增强共享组件而非另起炉灶

**禁止**：
- ❌ 手写 `<div class="empty-state">暂无数据</div>` — 用 `<EmptyState>` 组件
- ❌ 手写 `<div v-if="error" class="xxx-error">{{ error }}</div>` — 用 `<ErrorState>` 组件

## 模块结构一致性

每个模块目录必须包含（digital-human 占位页面除外）：

```
modules/{name}/
├── index.vue       ← 页面容器
├── api.js          ← HTTP 封装（即使只导出 1 个函数）
├── routes.js       ← 路由定义
├── components/     ← 子组件（即使只有 1 个）
└── composables/    ← 状态/逻辑（即使只有 1 个）
```

**禁止**：
- ❌ 模块目录放独立 `.css` 文件 — 样式必须在 `<style scoped>` 或 `tokens.css` 中
- ❌ 模块目录放 `store.js` / `stores/` — Pinia store 仅在 workflow 模块允许（Blockly/VueFlow 复杂状态机）
- ❌ `index.vue` 的 `<script setup>` 中直接写超过 20 行的 fetch/业务逻辑 — 抽到 composable

## Vite Proxy 配置

```
/api  /ws  → :8765 (Django)
/agentscope → :8000 (AgentScope)
```

WebSocket URL 必须走 Vite 代理（用 `wsUrl('/ws/...')`），禁止直连 `:8765`。

## Element Plus 陷阱

**el-cascader**: `emitPath` 默认 `true` → v-model 绑定路径数组 `[1,5]`，后端期望单个 ID。必须显式 `emitPath: false`。

使用不熟悉的复杂组件（el-cascader/el-tree-select/el-transfer）时：查文档确认默认值 → 确认 v-model 类型与后端一致 → `grep` 已知陷阱 → curl 往返验证。

## 页面空白排查

全局 CSS 继承是最隐蔽的坑 — scoped 内代码正常，但 `style.css` 覆盖了关键属性。看 DevTools Computed 面板的**最终值和来源文件**。尤其 `flex-direction` 被全局继承为 column 时。

## 质量门禁

```bash
# 编译
cd frontend && npx vite build --mode development 2>&1 | tail -10

# 样式自查
grep -rnP "color:\s*#[0-9a-fA-F]{3,6}|background:\s*#[0-9a-fA-F]{3,6}" \
  frontend/src/modules/ --include="*.vue" | grep -v "tokens\|style.css"

# el-cascader emitPath 陷阱
grep -rn 'el-cascader' frontend/src/modules/ | grep -v 'emitPath'
```

### 浏览器验证（改以下文件必须）
| 改动 | 验证 |
|------|------|
| router/routes | 点侧边栏每个菜单 → 确认加载 |
| api-client | 登录 → 刷新 → 不跳回登录页 |
| ChatView/SSE | 发一条消息 → 流式回复正常 |
| LoginView | 登录 → 跳转 dashboard |
| AppSidebar | 7 个菜单项完整 |

## 自评

1. 10 分钟能加一个 CRUD 页面？→ 模式一致
2. 改一个颜色全局生效？→ 令牌驱动，无硬编码色值
3. 新页面含 loading / empty / error 三态？→ 数据加载契约完整
4. 删一个模块不影响其他？→ 无跨模块网状 import
5. 没有新建 Pinia store / 独立 .css / 手写空状态？→ 共享组件优先
