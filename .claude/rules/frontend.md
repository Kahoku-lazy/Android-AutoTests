# Frontend Rules — Android-AutoTests

> 只放 AI 无法从代码中推断的红线、陷阱、惯例。其余自行读代码。

---

## 一、架构红线

- **模块间不互相 import** — 跨模块通信走 `router.push`（跳转）、`shared/components/`（共享组件）、`event-bus`（通知）
- **调用链单向** — `components/ → composables/ → api.js`，上层不反向引用下层
- **组件不直接调 axios** — API 调用必须经由 composable 或 store

## 二、代码红线

| 规则 | 阈值 |
|------|------|
| `.vue` 文件硬上限 | **500 行** |
| 组件拆分信号 | ref > 6 个 / 模板 > 150 行 / 有独立视觉区域 / 总行 > 300 |
| 状态管理选型 | 能用 `ref` 不用 Pinia；event bus 只做通知不传数据 |
| JSON 字段 | **snake_case**（与 JS camelCase 不同，容易写错） |

## 三、样式红线

1. **色值从 `tokens.css` 取**，禁止组件内硬编码 `#xxx`
2. **禁止封装薄 wrapper**（如把 `<el-button>` 包一层 `<MyButton>`）
3. **CSS 变量安全边界** — ECharts/Canvas/SVG 库的 JS 配置中 `var(--x)` **无效**，必须用字面量 `#xxx`

## 四、数据红线

- **禁止硬编码假数据** — `ref([{id:1}])` 或 computed 拼接头对象都不行，只能从 API 赋值
- **写操作不可静默吞错** — `catch(_){}` 必须改为至少 `console.error` + 用户提示
- **列表组件覆盖三态** — loading / error+重试 / empty / 正常
- **错误处理三层** — api-client 拦截器（网络层）→ composable（业务层，`ok:false` 时 ElMessage）→ 模板（视图层 v-if）

## 五、组件嵌套 — 探索方式

项目同时使用 Element Plus 和 animal-island-vue，组件嵌套时有隐藏冲突：

- **animal-island-vue Modal 内禁止用 `<Select>`** — Modal 的 `overflow:hidden` + `clip-path` 会裁剪下拉列表。必须用 `el-select`（Teleport 到 body）
- **改组件前先读 DOM** — 不要只看 Vue 模板，打开浏览器 DevTools Elements 面板看实际渲染的 DOM 层级。模板中 `<Card>` 可能渲染出 5 层 div
- **`!important` 泛滥的根因是嵌套过深** — 如果发现自己在写 `!important`，先检查是否可以用 `:deep()` 或减少嵌套层级

## 六、表格修改 — 注意事项与验收

- **列定义与模板 slot 必须一致** — `columns[i].dataIndex` 必须对应 `<template #cell-xxx>` 的 slot 名。改动 columns 后 grep 确认每个 dataIndex 都有对应 slot
- **表格改动影响面** — 修改 columns 或 AppTable props 后，必须验证：
  1. 表格视图正常渲染（所有列有数据）
  2. 如有卡片视图（device-pool），卡片也正常
  3. 分页切换正常（pageSize 切换，上一页/下一页）
  4. 响应式断点正常（缩小浏览器窗口到 900px 以下）
- **device-pool 的双视图** — 表格和卡片共享同一份数据，改表格 columns 或筛选逻辑时必须两个视图都验收

## 七、陷阱

- **el-cascader** `emitPath` 默认 `true` → 绑定 `[1,5]` 而非 `5`。必须显式 `emitPath: false`
- **页面空白先查 CSS** — DevTools Computed 面板看 `flex-direction` 是否被全局 CSS 继承为 column
- **跨模块 import 不受 lint 阻止** — 写之前确认目标是 shared/ 还是别的模块

## 八、质量门禁（改动后必跑）

```bash
# 编译
cd frontend && npx vite build --mode development 2>&1 | tail -5

# 模块加载
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/src/modules/{name}/index.vue

# 令牌合规（不应有新硬编码色值）
grep -rnP '(color|background|border|fill)[^;]*#[0-9a-fA-F]{3,6}' \
  frontend/src/modules/{name}/ --include="*.vue" --include="*.css" \
  | grep -v "tokens\|ECharts\|Canvas\|prototype"

# 空 catch（应为 0 行）
grep -rn "catch\s*(\s*_\s*)\s*{" frontend/src/modules/{name}/ --include="*.vue" --include="*.js"

# 超大文件
find frontend/src/modules/ -name "*.vue" | xargs wc -l | sort -rn | head -10
```
