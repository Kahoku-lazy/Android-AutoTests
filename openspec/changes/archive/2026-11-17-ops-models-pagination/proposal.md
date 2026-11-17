# 模型配置页：常驻翻页（每页 10 条）+ 清掉多余的横向滚动条

## Why

模型配置已经涨到 9~12 条，这一页仍是「一次铺开全部」：没有翻页、表格底部还挂着一条没有用的横向滚动条（滚动条本身也占掉一行视觉重量）。运营另外两页（用户管理、Agent 配置）都已是「页码文案 + 常驻上下页、每页 10 条」，这一页是最后一个例外。

## What Changes

- 控制区拆两行：第一行「搜索 + 新建模型」，第二行**常驻**的「第 X / Y 页 · 共 N 条」+「上一页 / 下一页」，每页固定 **10 条**。
- 计数从第一行下沉到页码文案（同一个数字不再写两遍），与用户管理 / Agent 配置同序。
- 分页在本页前端切片（`OPS_MODEL_PAGE_SIZE = 10`）；关键字一变回第 1 页；删除后越界自动夹回末页。
- 顺带修掉表底那条无用的横向滚动条：固定布局下 `el-scrollbar` 的 wrap 比容器多算 10px，被浏览器画成原生横条；在运营作用域内 `overflow-x: hidden`（EP 自己的横向滚动条本就 `display: none`，不丢可达内容）。
- 控制区三块间距提到 16px，与 Agent 配置页一致。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ops-model-config`：修改「模型配置列表的表格形态」——加入分页与横向滚动条要求。

## Impact

- 前端 `ops-console`：`model-configs.vue`（两行控制区 + 前端切片 + `.ops-section` 间距）、`constants.ts`（`OPS_MODEL_PAGE_SIZE`）、`table.style.css`（隐藏无用的横向滚动条）。
- 不动接口、不动后端、不动新建 / 编辑抽屉。
