
## 代码编写规范

1. 组件文件（.vue）只负责 UI 渲染和事件绑定。严禁在组件内编写复杂的业务逻辑、数据处理算法或正则解析
2. 严禁在组件内直接使用 fetch 或 axios；组件必须走模块 `api.js` / `api/*.ts`
3. 严禁在代码中直接使用魔法字符串（Magic Strings）或硬编码的正则
4. Vue 组件文件名必须使用 PascalCase（大驼峰），且后缀必须为 .vue
5. API/认证类 composable 不做表单校验；校验与 ElMessage 警告放在调用方（handleXxx）
6. 公开 TypeScript 签名与实现参数必须同步；禁止实现多参、导出类型少参；单测随职责迁移
7. 新 SVG 图标在 `shared/icons/index.ts` 用 `makeIcon` 导出；禁止无必要的独立 `IconXxx.vue`
8. 抽 shared 组件等第二个真实消费方；单处使用不提前抽象
9. 写操作禁止空 `catch` 静默吞错
10. 状态管理：`ref` → composable → Pinia（不可跳级）；新模块默认不用 Pinia（现存特例：workflow、device-inspector）
11. 必用共享件（场景→组件见下方「共享组件速查」）；禁止同场景自建

## 命名

| 场景 | ✅ | ❌ |
|------|----|----|
| 包装后再调用的内部函数 | `baseSwitchMode` / `rawSwitchMode` | `_switchMode`（易被当成未使用） |
| 仅编排用的 handler | `handleLogin` / `handleRegister` | 强行动态统一牺牲类型 |
| 校验失败文案 | `firstError \|\| '请完善表单'` | 假定 errors 非空直接 warning |

## 代码拆分规范

1. 当vue代码行数超过 500 行时，请务必进行代码拆分，先拆分**样式层**，再拆分**逻辑层**。

## 样式工程约束

1. 组件嵌套深度 MAX 4 层（页面容器 → 区域 → 卡片/表格/面板 → 内容元素），禁止 Level 5
2. z-index 层级：90 侧边栏 / 80 抽屉 / 70 弹窗 / 60 下拉 / 50 固定头部 / 0 内容区
3. 文件组织：模块 scoped CSS 放 .vue；跨模块共享样式 + Element Plus 覆盖放 `tokens.css`（`--app-*` / `--el-*`）；禁止在 style.css 全局写模块专属样式
4. CSS 变量安全边界：Canvas / ECharts / 动态 SVG 渲染不解析 CSS 变量，用字面量色值；改 `tokens.css` 后同步更新 JS 渲染配置
5. **块注释禁嵌 `*/`**：`tokens.css` / 任意 `.css` 的 `/* ... */` 内不得出现字面量 `*/`（`--foo-*/--bar` 会提前结束注释，后续 `:root` 令牌全部失效）。列举用顿号或 `、`，不要用 `/` 拼接。症状：页面退回无样式、`getComputedStyle` 上 `--ink` 为空、标题变 Times New Roman。改完 `tokens.css` 必须在浏览器确认 `--ink` 有值。
6. 新模块脚手架：`modules/{name}/` 含 index.vue / api.js / routes.js / components/ / composables/，复制设计系统模板改字段

## 默认拒绝的重构

- 动态 `component :is` 硬合并不同 props 卡片
- 整表 `reactive` 连锁大改（5+ 文件）
- 首屏关键图 `loading="lazy"`（伤 LCP）
- 1～2 处路径硬编码就抽路由常量
- 无行为变化的 `computed` 间接层
- 工作正常的 CSS `@import` 大治理（需 E2E，单独排期）
- 纯展示子组件为「配套重构」而改（只改契约/图标/bug/a11y）

**允许的低成本改进**（样式靠 class、无行为变化时可顺手做）：语义标签 `header`/`main`/`footer`、`aria-label`、装饰图 `alt=""`、解构分组注释。

## 暂缓项触发表（登录）

> 默认不做；仅当触发条件满足时再开改。

| 改动 | 暂缓理由 | 触发条件 |
|------|----------|----------|
| `LoginErrorOverlay` → `@/shared/components/MessageOverlay` | 仅 1 处消费 | 第二个页面需要全局消息弹窗 |
| CSS `@import` 治理（`login-card.css` / `auth-form-card.css`） | 现网正常；动构建顺序需 E2E | 出现样式覆盖 bug，或引入 CSS Modules |
| `/dashboard` 抽成路由常量 | 仅 2 处硬编码，收益低 | 出现第 3 处相同路径硬编码 |
| `useLoginForm` 位置参数 → 对象参数 | 仅 1 处调用方 | 第二个模块要复用 `useLoginForm` |
| `LoginViewState` 去掉对外暴露的 `accountList` | 影响面小 | 做 composable 接口清理时一并处理 |

## 改前流程（动手前必走）

1. 需求模糊 → 列 3～5 个具体理解让用户选，禁止默默挑一种执行。
2. 读目标 `.vue` 的 **template + script + style 三块**；改 CSS 前提取模板中全部 class（防止漏 inner class，凭印象重写会漏 12+ 个 inner class 返工 5 轮）。
3. 查约束：`.claude/rules/frontend.md`（本文）· `frontend/CLAUDE.md` §2（风格规则）· `frontend/src/shared/styles/tokens.css`（风格值：**先读头部「现行 / @deprecated / 待收敛」声明再取 token**）· 组件做法 `doodle-craft` skill。
4. 判边界跳转：纯 UI/样式 → 只改 CSS 不改逻辑；数据/API → 对照 `dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md`；AI 对话 → SSE 事件契约；跨界按序执行。

## 模块专属约束

> 已迁入各模块文件 `frontend/src/modules/{name}/CLAUDE.md`（唯一现行落点）。模块专属约束变更 → 只改对应模块文件，不再同步本文。

| 模块 | 落点 |
|------|------|
| dashboard / device-pool / device-inspector / element-locator / case-manager / test-runner / report-generator / workflow / ai-assistant | `frontend/src/modules/{name}/CLAUDE.md` |

## 状态管理决策树

按顺序选择，**不可跳级**：

| 优先级 | 方案 | 适用场景 | 示例 |
|:--:|------|------|------|
| 1 | `ref` / `reactive` | 组件内状态，不跨组件共享 | 表单输入、弹窗显隐、筛选条件 |
| 2 | composable | 同模块内多组件共享，或有复用价值 | `useElementTree()`、`useTaskWebSocket()` |
| 3 | Pinia store | 跨模块共享 + 需持久化 + 复杂状态机 | 设备连接状态、工作流编辑器画布 |

**升级信号**：ref 被 3+ emit 传递 → composable；composable 被 2+ 模块 import → shared/；composable 有 5+ 依赖 ref → Pinia。
**禁止**：新模块默认用 Pinia（先 ref 起步）；在 shared/ 之外新建 Pinia store（现存特例：workflow、device-inspector 各持有模块内 store）。
**localStorage** 仅用于持久化偏好（视图模式/主题），key 格式统一。

## 共享组件速查

以下场景**必须用共享组件，禁止自建**：

| 场景 | 组件 | 场景 | 组件 |
|------|------|------|------|
| 错误+重试 | `ErrorState` | 空数据 | `EmptyState` |
| 卡片布局 | `AppCard` | 数据表格 | `AppTable` |
| Tab 切换 | `AppTabs` | 树形面板 | `GroupTreePanel` |
| KPI 统计 | `KpiCard` | 筛选标签 | `FilterTabs` |
| 骨架屏 | `SkeletonCard` | 确认按钮 | `ConfirmButton` |

## 数据加载踩坑

| # | ✅ 正确 | ❌ 错误 |
|---|--------|--------|
| 1 | `@retry="fetchData"`（命名函数） | `@retry="() => { ... }"`（内联箭头每次渲染重建） |
| 2 | `error.value = ''` 放 `data.status` 内（成功后清除） | `error.value = ''` 放 try 第一行（retry 时闪白） |
| 3 | `<template v-else>` 包裹全部内容 | 每个 `<section>` 各自写 `v-if="!error"` |
| 4 | 一个页面一个 ErrorState | 每个 tab slot 各放一个 |
| 5 | `finally { loading = false }` | 只在 try 关 loading（catch 永远转圈） |
