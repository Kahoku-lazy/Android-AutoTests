# Vue 3 文档页面地图

> 核对时间：2026-11-10，目录从 `cn.vuejs.org` 页面侧栏读出。
> 站点改版后若某条 404，抓任意一页读它的侧栏即可重建；不要按记忆猜路径。

## URL 模板

| 目标 | 模板 |
| --- | --- |
| 指南页 | `https://cn.vuejs.org/guide/<path>.html` |
| API 页 | `https://cn.vuejs.org/api/<path>.html` |
| 页面源文件（中文） | `https://raw.githubusercontent.com/vuejs-translations/docs-zh-cn/main/src/guide/<path>.md` |
| 页面源文件（英文） | `https://raw.githubusercontent.com/vuejs/docs/main/src/guide/<path>.md` |

- 去掉 `.html` 也返回 200（实测），但引用时保留 `.html`。
- `<path>` 与站点路径一一对应，API 页同理把 `guide` 换成 `api`。

## 指南（51 页）

### 开始（2）

- 简介 — `introduction`
- 快速上手 — `quick-start`

### 基础（13）

- 创建一个应用 — `essentials/application`
- 模板语法 — `essentials/template-syntax`
- 响应式基础 — `essentials/reactivity-fundamentals`
- 计算属性 — `essentials/computed`
- 类与样式绑定 — `essentials/class-and-style`
- 条件渲染 — `essentials/conditional`
- 列表渲染 — `essentials/list`
- 事件处理 — `essentials/event-handling`
- 表单输入绑定 — `essentials/forms`
- 侦听器 — `essentials/watchers`
- 模板引用 — `essentials/template-refs`
- 组件基础 — `essentials/component-basics`
- 生命周期 — `essentials/lifecycle`

### 深入组件（8）

- 注册 — `components/registration`
- Props — `components/props`
- **事件 — `components/events`**
- 组件 v-model — `components/v-model`
- 透传 Attributes — `components/attrs`
- 插槽 — `components/slots`
- 依赖注入 — `components/provide-inject`
- 异步组件 — `components/async`

### 逻辑复用（3）

- 组合式函数 — `reusability/composables`
- 自定义指令 — `reusability/custom-directives`
- 插件 — `reusability/plugins`

### 内置组件（5）

- Transition — `built-ins/transition`
- TransitionGroup — `built-ins/transition-group`
- KeepAlive — `built-ins/keep-alive`
- Teleport — `built-ins/teleport`
- Suspense — `built-ins/suspense`

### 应用规模化（6）

- 单文件组件 — `scaling-up/sfc`
- 工具链 — `scaling-up/tooling`
- 路由 — `scaling-up/routing`
- 状态管理 — `scaling-up/state-management`
- 测试 — `scaling-up/testing`
- 服务端渲染 (SSR) — `scaling-up/ssr`

### 最佳实践（4）

- 生产部署 — `best-practices/production-deployment`
- 性能优化 — `best-practices/performance`
- 无障碍访问 — `best-practices/accessibility`
- 安全 — `best-practices/security`

### TypeScript（3）

- 总览 — `typescript/overview`
- TS 与组合式 API — `typescript/composition-api`
- TS 与选项式 API — `typescript/options-api`

### 进阶主题（7）

- 使用 Vue 的多种方式 — `extras/ways-of-using-vue`
- 组合式 API 常见问答 — `extras/composition-api-faq`
- 深入响应式系统 — `extras/reactivity-in-depth`
- 渲染机制 — `extras/rendering-mechanism`
- 渲染函数 & JSX — `extras/render-function`
- Vue 与 Web Components — `extras/web-components`
- 动画技巧 — `extras/animation`

## API 参考（28 页）

路径相对 `https://cn.vuejs.org/api/`。

> 版本徽标：`useTemplateRef()`、`useId()` 这类标题后面挂 `<sup class="vt-badge" data-text="3.5+" />`。
> 徽标文字在 `data-text` 里，抓成纯文本会丢；要判版本看 raw Markdown 或页面源码。

### 全局 API（2）

- 应用实例 — `application`
- 通用 — `general`

### 组合式 API（7）

- setup() — `composition-api-setup`
- 响应式: 核心 — `reactivity-core`
- 响应式: 工具 — `reactivity-utilities`
- 响应式: 进阶 — `reactivity-advanced`
- 生命周期钩子 — `composition-api-lifecycle`
- 依赖注入 — `composition-api-dependency-injection`
- 辅助 — `composition-api-helpers`

### 选项式 API（6）

- 状态选项 — `options-state`
- 渲染选项 — `options-rendering`
- 生命周期选项 — `options-lifecycle`
- 组合 — `options-composition`
- 其他杂项 — `options-misc`
- 组件实例 — `component-instance`

### 内置内容（4）

- 指令 — `built-in-directives`
- 组件 — `built-in-components`
- 特殊元素 — `built-in-special-elements`
- 特殊 Attributes — `built-in-special-attributes`

### 单文件组件（3）

- 语法定义 — `sfc-spec`
- `<script setup>` — `sfc-script-setup`
- CSS 功能 — `sfc-css-features`

### 进阶 API（6）

- 自定义元素 — `custom-elements`
- 渲染函数 — `render-function`
- 服务端渲染 — `ssr`
- TypeScript 工具类型 — `utility-types`
- 自定义渲染 — `custom-renderer`
- 编译时标志 — `compile-time-flags`

## 入口页

| 用途 | URL |
| --- | --- |
| 文档首页 | `https://cn.vuejs.org/guide/introduction.html` |
| API 索引 | `https://cn.vuejs.org/api/` |
| 互动教程 | `https://cn.vuejs.org/tutorial/` |
| 示例 | `https://cn.vuejs.org/examples/` |
| 术语表 | `https://cn.vuejs.org/glossary/` |
| 错误码 | `https://cn.vuejs.org/error-reference/` |
| 版本发布 | `https://cn.vuejs.org/about/releases.html` |
> `about/releases.html` 只讲发布周期与支持窗口，**不逐特性列版本**；某个 API 从哪版开始，看 API 页徽标、指南原文或 core 仓库的 `CHANGELOG.md`（如 `https://raw.githubusercontent.com/vuejs/core/v3.5.0/CHANGELOG.md`），版本稳定的结论可引 Vue 博客（如 `https://raw.githubusercontent.com/vuejs/blog/main/posts/vue-3-4.md` 的「defineModel is Now Stable」）。
| FAQ | `https://cn.vuejs.org/about/faq.html` |
| Vue 2 文档（**不要**用于 3.x 回答） | `https://v2.cn.vuejs.org/` |

## 已验证的深链接（页面内实际给出的锚点）

| 主题 | URL |
| --- | --- |
| 触发与监听事件 | `https://cn.vuejs.org/guide/components/events.html#emitting-and-listening-to-events` |
| 事件参数 | `https://cn.vuejs.org/guide/components/events.html#event-arguments` |
| 声明事件 | `https://cn.vuejs.org/guide/components/events.html#declaring-emitted-events` |
| 事件校验 | `https://cn.vuejs.org/guide/components/events.html#events-validation` |
| `defineEmits()`（合并锚点） | `https://cn.vuejs.org/api/sfc-script-setup.html#defineprops-defineemits` |
| `defineModel()` | `https://cn.vuejs.org/api/sfc-script-setup.html#definemodel` |
| `defineSlots()` | `https://cn.vuejs.org/api/sfc-script-setup.html#defineslots` |
| `useModel()` | `https://cn.vuejs.org/api/composition-api-helpers.html#usemodel` |
| `useTemplateRef()` | `https://cn.vuejs.org/api/composition-api-helpers.html#usetemplateref` |
| `useId()` | `https://cn.vuejs.org/api/composition-api-helpers.html#useid` |
| ref 声明 | `https://cn.vuejs.org/guide/essentials/reactivity-fundamentals.html#ref` |
| v-on 监听器透传 | `https://cn.vuejs.org/guide/components/attrs.html#v-on-listener-inheritance` |
| 组件事件类型标注 | `https://cn.vuejs.org/guide/typescript/composition-api.html#typing-component-emits` |
| 模板引用类型标注 | `https://cn.vuejs.org/guide/typescript/composition-api.html#typing-template-refs` |

## 本仓库常查的主题 → 页面

| 要查什么 | 去哪 |
| --- | --- |
| props / emits / v-model / slots / attrs | `guide/components/*`，签名以 `api/sfc-script-setup` 与 `api/options-state` 为准 |
| 响应式（ref / reactive / computed / watch） | `api/reactivity-core`、`api/reactivity-utilities`、`guide/essentials/*` |
| 生命周期顺序 | `guide/essentials/lifecycle`、`api/composition-api-lifecycle` |
| 组件类型标注 | `guide/typescript/composition-api`、`api/utility-types` |
| 路由 / 状态管理 | `guide/scaling-up/routing`、`guide/scaling-up/state-management`（细节去 Vue Router / Pinia 自己的文档） |
| 性能与无障碍 | `guide/best-practices/performance`、`guide/best-practices/accessibility` |
