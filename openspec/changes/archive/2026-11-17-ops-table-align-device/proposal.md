# 运营两张表：向设备管理的表纸与字号口径对齐

## Why

运营后台两张表（`/ops/users`、`/ops/model-configs`）底子已是共享 `AppTable` + 模块色 `accent`，但与设备管理、BUG 单两张已整改的表并排时明显不是一套语言：正文 12px 平铺、表纸带赭橙 4px 硬影 + 竖网格线、外层还套一层 `.doc-section` 框；用户表把「账号 / 邮箱」拆成两列、时间直接渲染 ISO 原文被截断；控制区分三行且保留了「显示行数 10/20/50/100」四键，而设备 / 任务 / BUG 三页早已固定行数。

## What Changes

- **表纸**：两页都改「无影变体」——保留共享描边与圆角，模块作用域内去掉赭橙位移硬影；去掉 `:border`，不再画网格线；去掉 `.doc-section` 外框，表纸成为页面里唯一的框。
- **字号三档**：表头 16（全局定义 + 居中 + 图标）、正文 14、次级 12（邮箱、绝对时间）。抽屉里的身份 / 状态 chip 同步到 14px 同一皮肤。
- **用户表结构**：8 列 → 7 列。账号首列改身份单元（首字母头像 + 账号 + 邮箱副行）；注册 / 最后登录两列改「相对时间 14 + 绝对时间 12」双行；操作列保留单个「管理」胶囊。
- **模型表结构**：6 列 → 5 列。模型名做首列身份单元（副行给厂商 · 类型 · 音色），类型列紧随其后改为 chip，操作列由「编辑 + 删除」两个等权按钮收敛为「编辑胶囊 + ⋯ 菜单（删除）」。
- **控制区**：用户表三行 → 两行（批量动作 / 页码 + 筛选 + 搜索 + 翻页），下线「显示行数」四键、每页固定 10 条；模型表加关键字搜索（前端过滤）。
- **登记**：`frontend-doodle-sketch-table` 的「无影页清单」加入运营两页。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ops-user-console`：新增「用户列表的表纸、字号与首列身份单元」要求。
- `ops-model-config`：修改「列表展示模型类型」（类型 chip 紧随模型首列），新增「模型配置列表的表格形态」要求。
- `frontend-doodle-sketch-table`：无影页清单加入运营两页。

## Impact

- 前端 `ops-console`：`index.vue`、`model-configs.vue`、`index.style.css`、新增 `table.style.css`、新增 `components/OpsUserIdentityCell.vue` / `components/OpsModelIdentityCell.vue`、新增 `helpers/datetime.ts`、`constants.ts`、`composables/useOpsUsers.ts`、`components/OpsUserDrawer.vue`（chip 皮肤对齐）。
- 测试：`tests/ops-console/p0/ops-users.spec.ts`（每页固定 10 条，移除已下线的改行数用例）、`model-configs.spec.ts`（类型列位置）、`ops-nav.spec.ts`（侧栏运营三入口不同色的既有断言修正）。
- 不动后端、不动接口、不动共享件（`AppTable` / `workbench-theme.css` / `tokens.css` 均不改）。
