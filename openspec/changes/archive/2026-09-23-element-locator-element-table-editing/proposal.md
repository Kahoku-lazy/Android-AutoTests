## Why

元素定位页面叶子打开后的元素表目前**只能改两格**：`PageElementsWorkbench.vue` 仅提供别名与测试点的行内编辑，其它定位字段（文本、resource-id、XPath、坐标）只读；后端 `PUT /api/elements/items/{id}/` 的白名单也只有 `alias / tags / notes / is_test_point`。表格一次渲染最多 500 条（`apiPageItems(..., 500)`）且没有分页；既不能手写新增一行元素，也没有行删除入口——手写一条定位只能靠设备检查器抓快照导入。结果是导入进来的元素一旦某列有误（XPath 选错、坐标需手调），用户只能重新抓快照。

## What Changes

- 元素表改为**每页固定 10 行**分页（「第 X / Y 页 · 共 N 条」+ 上一页 / 下一页），默认第 1 页；数据源改用接口既有的 `offset` / `limit` 与 `total`，不再一次性取 500 条。
- **定位业务列全量行内可编辑**：别名、文本、content-desc、class、resource-id、XPath、bounds（坐标）、测试点、备注；单元格默认只显示纯文本，**双击**才进入编辑态（Enter 提交 / Esc 取消 / 失焦提交）；`x` / `y` / `width` / `height` 由 bounds 解析后同步写入（不单列编辑）；系统列（id / 缩略图 / 创建时间 / depth / index）MUST 只读。
- 每格 **逐列校验**：bounds 必须匹配 `[x1,y1][x2,y2]`、数字列非负整数、字符串长度不超模型列宽、XPath 输入合法；非法值 MUST 拒绝并提示，MUST NOT 写库。
- 新增 **「+ 新增一行」**：别名必填；resource-id 与 bounds **至少填一个**（两者都空直接拒绝，避免撞 `(page, resource_id, bounds)` 唯一约束）；校验通过后写入该页面并刷新列表。
- 新增 **行勾选 + 批量删除**：勾选多行、二次确认后整批删除（原子）；删除的是**元素行**，不是页面。
- XPath 可编辑的写入口径：保存时该行 `xpath_candidates` 覆盖为 `[{type: "manual", xpath: <输入值>, count: 1}]`（丢弃导入时的其余候选）。
- 后端：`PUT /api/elements/items/{id}/` 扩写白名单与逐列校验；新增元素批量删除端点；两处写库统一收敛到 `element_locator/api.py`。
- **不改**：检查器快照导入链路、`el_elements` 表结构与 `(page, resource_id, bounds)` 唯一约束、目录树能力。

## 关联文档

- PRD-04（元素定位）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `element-locator-page-workbench`: 元素工作台从「全量渲染 + 仅别名/测试点可编辑」改为「每页 10 行分页 + 定位业务列全量行内可编辑 + 逐列校验 + 新增一行 + 行勾选批量删除」，并新增元素行增删改的写库接口契约。

## Impact

- 前端：`frontend/src/modules/element-locator/components/PageElementsWorkbench.vue`（分页、全列行内编辑、新增行、勾选批量删除）、`api.ts`（更新 / 新增 / 批量删除封装）、新增 `helpers/` 逐列校验纯函数（可单测）
- 后端：`apps/element_locator/api.py`（扩写 `update_element`、新增元素批量删除写函数）、`apps/element_locator/views_page_elements.py` 与 `views_page_element_batch.py`（校验收口与响应）、`apps/element_locator/urls.py`（新路由）
- 测试：后端新增 `tests/graybox/integration/test_element_row_crud.py`（新增 / 校验拒绝 / 批量删除）；前端在 `frontend/tests/element-locator/p0/` 增补校验纯函数与 api 封装用例
- 文档：元素定位接口文档补记新端点与校验口径
- **不动**：`el_elements` 表结构与唯一约束、检查器导入链路、目录树与文件详情页骨架
