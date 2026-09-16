# Frontend AGENTS.md

## 技术规范
1. 编程语言： TypeScript 5.4 
2. 前端框架： Vue 3.4 + Vite 5 + Element Plus
3. 状态管理： Pinia
4. 其它技术： Vue Router、ECharts、Mermaid、@vue-flow、axios 

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

### 布局区域与归属

1. 区域（L0–L5）是 UI 的横切分层：L0:视口 →  L1: 侧栏/主区 → L2:页头/页面根 → L3:容器 → L4:数据面 → L5:覆盖层
2. 模块拥有自己页面的 **L2–L5**，**不拥有 L1**
3. 跨模块的组件放在 `shared/` 中


## Vue 代码编写规范

### 1. 硬性规范

1. 组件文件（`.vue`）只负责 UI 渲染和事件绑定。严禁在组件内编写复杂的业务逻辑、数据处理算法或正则解析

2. 严禁在代码中直接使用魔法字符串（Magic Strings）或硬编码的正则

3. Vue 组件文件名必须使用 PascalCase（大驼峰），且后缀必须为 .vue

4. 公开 TypeScript 签名与实现参数必须同步；禁止实现多参、导出类型少参；单测随职责迁移

5. 新 SVG 图标在 `shared/icons/index.ts` 用 `makeIcon` 导出；禁止无必要的独立 `IconXxx.vue`

6. 当 vue 代码行数超过 500 行时，请务必进行代码拆分，先拆分**样式层**，再拆分**逻辑层**。

7. 字号只能取 `tokens.css` 的字号刻度（T0 原子 `--font-size-*`；过渡期 `--app-size-*` 为等价别名，最小 12px），禁止硬编码 `font-size` 字面量。
