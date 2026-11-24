# frontend · 项目结构

> 归属模块：`frontend/` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/public/`、`frontend/src/`、`frontend/src/router.ts`、`frontend/src/shared/`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

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
└── helpers/         # 纯函数（无状态无副作用）
```

### 布局区域与归属

1. 区域（L0–L5）是 UI 的横切分层：L0:视口 →  L1: 侧栏/主区 → L2:页头/页面根 → L3:容器 → L4:数据面 → L5:覆盖层
2. 模块拥有自己页面的 **L2–L5**，**不拥有 L1**
3. 跨模块的组件放在 `shared/` 中
