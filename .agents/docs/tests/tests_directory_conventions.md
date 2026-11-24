# tests · 目录约定与迁移状态

> 归属模块：`tests/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/pytest.ini`、`tests/conftest.py`、`tests/test_settings.py`、`tests/` 目录结构
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## 目录约定（按模块分类，模块内再按测试类型）

**一级按被测功能（模块）分，二级才是测试类型**。新增测试一律按此放置：

```
tests/
  <模块>/
    api/            # 灰盒（接口）：功能链路 + 末尾落库校验
    integration/    # 灰盒（服务层）：Django ORM / 多模块协作
    e2e/            # 浏览器 b2b：真实浏览器点交互（需要时才有）
  arch/unit/        # 契约守护（例外，唯一保留的 unit 目录）
```

- `<模块>` = 被测功能的归属（`models` / `config` / `dashboard` / `ai_assistant` / `device` …），
  不是被测文件的路径照抄。
- **不再有 `tests/<模块>/unit/`**：业务单元测试已退役，写代码时临时放在 `temps/`（见 `tests/AGENTS.md`）。
- pytest marker（`api` / `integration` / `e2e` / `arch`）**仍然按测试类型打**，与目录分类正交；
  `unit` marker 现在只被 `tests/arch/unit` 使用。
- 每级目录都要有 `__init__.py`（`tests/` 是包，缺一层会让 pytest 把同名目录当同一个包而导入冲突）。

## 迁移状态

平台模块：`dashboard` / `ai_assistant` / `knowledge_search` / `device` / `serial_log` / `task` / `case` / `report` / `bug_ticket`；
跨模块一致性在 `arch/`。

| 目录 | 内容 | 状态 |
|---|---|---|
| `arch/unit` | 跨模块契约守护（API 路径、鉴权姿态、表单校验、前端 DTO、日志、DB 预检） | ✅ 唯一保留的 unit |
| `dashboard/{api,unit}` | 仪表盘（`unit` 已迁出） | 灰盒在 `api` |
| `ai_assistant/api` | 平台助手 / 模型配置 / 角色 / SOP / 评估（`unit` 已迁出） | ✅ |
| `knowledge_search/{api,integration}` | 知识库检索与评估（`unit` 已迁出） | ✅ |
| `device/{api,integration}` | 设备管理（`unit` 已迁出） | ✅ |
| `serial_log/{api,integration}` | 串口日志（`unit` 已迁出） | ✅ |
| `task/api` | 任务清单（`unit` 已迁出） | ✅ |
| `case/{api,integration}` | 用例管理（`unit` 已迁出） | ✅ |
| `report/integration` | 测试报告（`unit` 已迁出） | ✅ |
| `bug_ticket/api` | bug 单管理（`unit` 已迁出） | ✅ |
| `auth/{api,e2e}` | 登录鉴权：接口用例 + 登录 b2b | ✅ |
| `ops_console/api` | 运维控制台 | ✅ |
| `usage_ledger/unit` | 用量账本 | ❌ 已迁出（`temps/tests-unit-archive/`） |
| `config/unit`、`models/unit`、`engines/{ae_harness,backend_bridge,device}/unit` | 配置 / 模型 / 引擎 | ❌ 已迁出（`temps/tests-unit-archive/`） |
| `api_kit/` | 灰盒共享设施：`loader.py` / `schemas.py` | ✅ |
| `api/` | 只留 `conftest.py`（夹具）与 `case/*.yaml`（用例数据） | 保留：契约守护硬编码了这两个路径 |
| `e2e/` | 只留共享设施：`conftest.py` / `selectors.py` / `step_report.py` | 保留：b2b 夹具 |

已删除：`graybox/`（迁移后清空）、`ai_planner/`（无测试代码）、`device_pool/`（迁入 `device/`）、
`page_flow/`（页面流退役）、`test_element_locator_views_split.py`（`backend/apps/element_locator` 已下线）、
`test_example_integration.py`（模板示例）；2026-11-24 再删全部 `tests/<模块>/unit/`（迁至 `temps/tests-unit-archive/`）。
