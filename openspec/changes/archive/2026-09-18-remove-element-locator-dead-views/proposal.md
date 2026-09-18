## Why

上一组变更（`refactor(element-locator): 删除与 router 重复的 legacy 路由，收敛为唯一实现`）删除了 18 条被 router 遮蔽的
legacy 手写路由。这些路由的**唯一引用者**消失后，它们的视图模块成了死代码 —— 但文件仍在，
会让读者以为平台还有第二套实现（平铺信封 `{status, pages|elements|groups|flows|endpoints}`）。

逐个核实（排除自身定义后统计引用）：

| 模块 | 内部符号 | 排除自身后的引用者 |
|---|---|---|
| `views_web.py`（196 行） | `list_web_elements` / `create_web_element` / `web_element_detail` / `batch_import_web_elements` | **0** |
| `views_flows.py`（120 行） | `flows_handler` / `delete_flow` / `web_flows_handler` / `delete_web_flow` | **0** |
| `views_web_groups.py` | `list_web_groups` / `web_group_detail` | **0**（仅被护栏测试 import） |
| `views_api_assets.py` | `list_api_groups` / `list_api_endpoints` / `api_group_detail` / `api_endpoint_detail` | **0**（仅被护栏测试 import） |
| `views_projects_drf.group_write_gone` | — | **0**（ViewSet 已改用 `GroupWriteRetired`） |

注：`api.py` 里也定义了同名的 `create_web_element` / `delete_flow` 等，那是**写原语**，与这些视图函数同名不同物，
不是引用。已在核实中逐一确认。

## What Changes

- 删除 4 个死视图模块：`views_web.py`、`views_flows.py`、`views_web_groups.py`、`views_api_assets.py`
- 删除 `views_projects_drf.py` 中已无人引用的 `group_write_gone`
- `tests/graybox/unit/test_element_locator_group_writes_removed.py`：原先 import 两个模块以断言
  「某些符号不存在」；模块本身删除后，断言改为**模块已不存在**（更强）+ 保留 `api.__all__` 的断言
- `dev_docs/DEV_TEST/接口文档/API-元素定位.md`：修正**三重过期**的描述 —— 它仍写着
  「router 带尾斜杠 / legacy 无尾斜杠两种信封可共存（由 `NormalizeTrailingSlashMiddleware` 保证）」，
  而这三点（legacy 路由、两种信封、该中间件）现在都不存在了

**Non-goals**：
- 不改任何路由、不改任何 API 行为 —— 本变更是纯删死代码
- 不动 `views_pages.py` / `views_page_elements.py` / `views_page_element_batch.py` / `views_snapshot.py`（pages / items 仍有路由指向它们）
- 不动 `api.py`（写原语全部在用）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 纯删死代码：`.openspec.yaml` 设 `skip_specs: true`（与 `2026-09-17-remove-login-dead-code` 同处置）。
> 不改变任何运行时行为 —— 被删的代码在删除前已不可达。

## Impact

- 后端：删除 4 个文件 + `views_projects_drf.py` 一处函数
- 测试：1 个护栏用例的断言方式调整
- 文档：1 个接口文档的过期段落
- API / 前端 / 依赖 / 数据库：**无**
