
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
12. JWT：`beforeEach` 守卫保护全部路由；Axios 拦截器自动处理 401 刷新
13. 当vue代码行数超过 500 行时，请务必进行代码拆分，先拆分**样式层**，再拆分**逻辑层**。

## 命名

| 场景 | ✅ | ❌ |
|------|----|----|
| 包装后再调用的内部函数 | `baseSwitchMode` / `rawSwitchMode` | `_switchMode`（易被当成未使用） |
| 仅编排用的 handler | `handleLogin` / `handleRegister` | 强行动态统一牺牲类型 |
| 校验失败文案 | `firstError \|\| '请完善表单'` | 假定 errors 非空直接 warning |

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

## CSS 布局修复模式（高频踩坑，来源 memory/css-*）

### 排查三步铁律（视觉问题先开 DevTools，不碰代码）

1. **查 DOM**：目标元素是否存在？class 是否正确？animal-island-vue 用 BEM 双下划线（`.animal-tabs__list`），不要凭记忆猜内部类名
2. **画高度链**：从 `<html>` 到目标逐层标 flex / min-height / overflow；`flex:1` 的父级必须有 `min-height:0`
3. **选滚动策略**（二选一，不混用）：视口固定 + 内层滚动，或内容撑开 + 页面整体滚动

### 高频修复模式

| 症状 | 根因 | 修复 |
|------|------|------|
| 页面下半截被截断/无法滚动 | flex 中 `min-height:0` + 父级 `overflow:hidden` 锁死高度 | 内层滚动 `.inner-scroll{flex:1;min-height:0;overflow-y:auto}`；页面滚动 `.doc-body{min-height:auto;overflow:visible}` |
| 布局错乱、装饰图被误匹配 | Vue scoped `:deep(> *)` 匹配所有直接子元素 | 改 `:deep(.具体class)`；禁止对通配符用 `:deep()` |
| 表格右侧大片空白 | 固定 px 列宽合计超容器 | 列宽改百分比 + `table-layout:fixed` + `width:100%` + `text-overflow:ellipsis` |
| Chart.js 横向滚动失效 / canvas 撑爆卡片 | `responsive:true` 按视口重算 canvas + Grid `min-width:auto` | `responsive:false` + 手动算像素宽 + Grid `minmax(0,1fr)` / `min-width:0` |

> 全局 CSS 冲突（如 `.doc-body { flex-direction:column }` 覆盖子组件横向布局）必须看浏览器 Computed 面板的**来源文件**列，scoped 内看不出。CLI（curl/vite build）捕获不了纯 CSS 问题。
