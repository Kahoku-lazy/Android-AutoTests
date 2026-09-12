# Frontend AGENTS.md

## 前端项目结构

### 静态资源文件文件路径：`public/`


### 前端源码文件路径：`src/`

1. 模块模版结构如下，各模块按需取用，非强制全套。
```
src/modules/{name}/  
├── index.vue        # 模块入口视图（路由挂载点）
├── routes.ts        # 模块路由（由 router.ts 汇总导入）
├── api.ts | api/    # HTTP 唯一出口（内部走 shared/api-client）
├── AGENTS.md        # 模块专属约束（红线/契约/协议特例/关单附加项）
├── constants.ts     # 常量/枚举（唯一真相源）
├── types.ts         # 模块 DTO
├── *.logic.ts       # 编排层（组合 composable + 提交前校验 + 清表单）
├── components/      # 私有业务组件（不跨模块复用）
├── composables/     # 状态与流程
├── helpers/         # 纯函数（无状态无副作用）
└── stores/          # Pinia（仅 workflow / device-inspector）
```

### 跨模块共享文件：`shared/`

1. 平台前端侧边栏代码文件如下

- shared/components/AppSidebar.vue
- shared/components/AnimatedMascot.vue
- shared/components/sidebarNavConfig.ts

2. 内容分块容器组件：AppCard

- 文件路径：`shared/components/AppCard.vue`
- 使用场景：图表卡 · 表格卡 · 状态/指标卡 · 分组卡（一组数据一块）· 认证卡（登录/注册/切账号）
- 一句话判据：把一组内容框成"块"就用它；单条数据的卡片（设备卡/任务卡）用模块私有组件
- 注意：外观仅在工作台外壳 `.wb-shell` 内生效（脱离后退化成 Element Plus 默认）

3. 数据表格组件：`AppTable`

- 文件路径：`shared/components/AppTable.vue`
- 使用场景：多行多列列表；某列要自定义渲染时用 `#cell-<prop>` 插槽（列用 `{title, dataIndex, width, align}` 数组声明）
- 注意：列宽写 `%` 会被丢弃并兜 `minWidth:120`（Element Plus 会塌列）；表格配工具栏/分页时才套 `AppCard`（`device-pool/index.vue:153` 是裸用）

4. 页签切换组件：`AppTabs`

- 文件路径：`shared/components/AppTabs.vue`
- 使用场景：同一区域切出不同内容 → `items` + 按 key 的插槽（与 `FilterTabs` 的区别：它承载内容）
- 注意：`leafAnimation` / `shadow` 无对应 CSS，传了没效果（3 个模块正在白传）

5. 筛选标签组件：`FilterTabs`

- 文件路径：`shared/components/FilterTabs.vue`（配 `shared/composables/useFilterTabs.ts`）
- 使用场景：列表顶部按状态/类型筛选；只切一个 key、不承载内容；带 `count` 才显示角标
- 用法：`useFilterTabs(source, tabDefs, matchFn)` 拿 `filterTabs` / `activeFilter` / `filteredItems`

6. 统计数字组件：`KpiCard`

- 文件路径：`shared/components/KpiCard.vue`
- 使用场景：指标行（一屏 4 个一排），常放进 `AppCard` 内
- props：`shape` 四态（diamond / triangle / square / circle）+ `color`（直接当颜色值，传 `var(--c-*)`）

7. 页面顶栏组件：`WorkbenchHeader`

- 文件路径：`shared/components/WorkbenchHeader.vue`
- 使用场景：每个页面顶部的工作台标题栏（16 个文件在用，覆盖 8 个模块）
- 注意：`actions` 插槽放 `el-button.wb-btn`，勿用其它按钮样式

8. 页面标题组件：`PageHeader`

- 文件路径：`shared/components/PageHeader.vue`
- 使用场景：页面 Hero 卡（当前仅 report-generator 3 个文件在用）
- 注意：`color` 是死 prop、传了没效果；新页面页头优先用 `WorkbenchHeader`

9. 四态占位组件：`shared/components/patterns/`

- `ErrorState`：错误 + 重试（`message` / `@retry`），一个页面只放一个
- `EmptyState`：空数据（`icon` / `text` / `hint`，插槽放 CTA）
- `SkeletonCard`：加载骨架（`lines`）
- `ConfirmButton`：危险操作二次确认（`message` / `@confirm`）
- 注意：`SkeletonCard`、`ConfirmButton` 目前各只有 1 个消费方，未达到规则 8 的"第二个真实消费方"


### 独立视图文件：`views/`


### 测试文件：`tests/`


## Vue 代码编写规范

> 规则唯一真相源：`.agents/skills/android-autotests-rules/references/frontend.md`；本节是该文件的常驻摘要，规则变更必须同步该文件。

### 1. 硬性规范

1. 组件文件（`.vue`）只负责 UI 渲染和事件绑定。严禁在组件内编写复杂的业务逻辑、数据处理算法或正则解析

2. 严禁在组件内直接使用 fetch 或 axios；组件必须走模块 `api.js` / `api/*.ts`

3. 严禁在代码中直接使用魔法字符串（Magic Strings）或硬编码的正则

4. Vue 组件文件名必须使用 PascalCase（大驼峰），且后缀必须为 .vue

5. API/认证类 composable 不做表单校验；校验与 ElMessage 警告放在调用方（handleXxx）

6. 公开 TypeScript 签名与实现参数必须同步；禁止实现多参、导出类型少参；单测随职责迁移

7. 新 SVG 图标在 `shared/icons/index.ts` 用 `makeIcon` 导出；禁止无必要的独立 `IconXxx.vue`

8. 抽 shared 组件等第二个真实消费方；单处使用不提前抽象

9. 写操作禁止空 `catch` 静默吞错

10. 状态管理：`ref` → composable → Pinia（不可跳级）；新模块默认不用 Pinia（现存特例：workflow、device-inspector）

11. 必用共享件（场景→组件见「2. 共享组件速查」）；禁止同场景自建

12. JWT：`beforeEach` 守卫保护全部路由；Axios 拦截器自动处理 401 刷新

13. 当 vue 代码行数超过 500 行时，请务必进行代码拆分，先拆分**样式层**，再拆分**逻辑层**。

### 2. 命名

| 场景 | ✅ | ❌ |
|------|----|----|
| 包装后再调用的内部函数 | `baseSwitchMode` / `rawSwitchMode` | `_switchMode`（易被当成未使用） |
| 仅编排用的 handler | `handleLogin` / `handleRegister` | 强行动态统一牺牲类型 |
| 校验失败文案 | `firstError \|\| '请完善表单'` | 假定 errors 非空直接 warning |
