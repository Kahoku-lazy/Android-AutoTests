# Agent 配置页：常驻翻页（每页 10 条）+ 控制区与表格拉开间距

## Why

`/ops/agents` 的列表把接口返回的全部 Agent 一次铺开：数据一多就整页滚动，「新建配置」那颗键又紧贴表头（间距只有 4px），点完新建视线直接撞进表头。用户管理与模型配置两页已经改成「控制区两行 + 固定每页条数」，这一页是运营三页里唯一还没翻页的。

## What Changes

- 「新建配置」单独一行，下面新增一行**常驻**的页码文案 + 「上一页 / 下一页」：只有一页时两键置灰但仍在（与用户管理同口径），每页固定 **10 条**。
- 控制区三块（新建行 / 翻页行 / 表格）之间的间距由 8px 提到 16px（`--app-space-md`），按键不再贴表头。
- 数据仍在一次请求里取全量，分页在本页前端切片（`OPS_AGENT_PAGE_SIZE = 10`）；删除后若当前页越界，自动夹回最后一页。
- 顺带移除已无消费方的 `.ops-count` 样式（「共 N 条」改由页码文案承担）。

## Capabilities

### New Capabilities

- `ops-agent-config`：Agent 配置页的列表分页与间距。

### Modified Capabilities

无。

## Impact

- 前端 `ops-console`：`agents.vue`（两行控制区 + 前端切片 + 引入模块骨架样式）、`constants.ts`（新增 `OPS_AGENT_PAGE_SIZE`）、`index.style.css`（删 `.ops-count`）。
- 不动接口、不动后端、不动抽屉表单。
