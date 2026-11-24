# tests · 目录约定与迁移状态

> 归属模块：`tests/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/pytest.ini`、`tests/conftest.py`、`tests/test_settings.py`、`tests/` 目录结构
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## 目录约定（按模块分类，模块内再按测试类型）

**一级按被测功能（模块）分，二级才是测试类型**。新增测试一律按此放置：

```
tests/
  <模块>/
    unit/           # 单元：灰盒、纯逻辑、零 I/O 零 DB
    integration/    # 集成：Django ORM / 多模块协作
    api/            # 接口：黑盒 HTTP（需要时才有）
    e2e/            # 端到端：真实浏览器 / 设备（需要时才有）
```

- `<模块>` = 被测功能的归属（`models` / `config` / `rag` / `agents` / `workflow` / `device` …），
  不是被测文件的路径照抄。
- pytest 主 marker（`unit` / `integration` / `api` / `e2e`）**仍然按测试类型打**，与目录分类正交。
- 每级目录都要有 `__init__.py`（`tests/` 是包，缺一层会让 pytest 把同名目录当同一个包而导入冲突）。

### 迁移状态

大模块（平台功能）：`dashboard` / `ai_assistant` / `knowledge` / `device` / `serial_log` / `task` / `case` / `report` / `bug_ticket`；
引擎统一在 `engines/`（按子模块再分层）；跨模块契约在 `arch/`。

| 目录 | 内容 | 状态 |
|---|---|---|
| `models/{unit,integration}` | 模型层 | ✅ |
| `config/unit` | 配置层（读表、加解密、结构） | ✅ |
| `dashboard/unit` | 仪表盘 | ✅ |
| `ai_assistant/unit` | AI 助手（含 planner / verifier 提示词与任务） | ✅ |
| `knowledge/{unit,integration}` | 知识库助理（文字 + 语音） | ✅ |
| `device/{unit,integration}` | 设备管理 | ✅ |
| `serial_log/unit` | 串口日志 | ✅ |
| `task/unit` | 任务清单 | ✅ |
| `case/{unit,integration}` | 用例管理 | ✅ |
| `report/{unit,integration}` | 测试报告 | ✅ |
| `bug_ticket/unit` | bug 单管理 | ✅ |
| `engines/agents/{unit,e2e}` | 引擎：agents（SOP / 角色 / 工具 / 中间件 / RAG / 语音） | ✅ |
| `engines/device/unit` | 引擎：device | ✅ |
| `arch/unit` | 跨模块契约（API 路径、枚举 SSOT、鉴权、日志、DB 预检） | ✅ |
| `auth/{api,e2e}` | 登录鉴权：4 个接口脚本 + 登录端到端 | ✅ |
| `<模块>/api` | 接口脚本已按模块归位（device / serial_log / dashboard / task / case / bug_ticket） | ✅ |
| `api_kit/` | 接口测试共享设施：`loader.py` / `schemas.py` | ✅ |
| `api/` | 只留 `conftest.py`（夹具）与 `case/*.yaml`（用例数据） | 保留：契约测试硬编码了这两个路径 |
| `e2e/` | 只留共享设施：`conftest.py` / `selectors.py` / `step_report.py` | 保留：端到端夹具 |

已删除：`graybox/`（迁移后清空）、`ai_planner/`（无测试代码、`planner_eval` 命令已不存在）、`device_pool/`（迁入 `device/`）、
`page_flow/`（页面流退役；`test_xpath_text_matches.py` 被测方法已随 engines 历史重构删除，失效用例经确认一并删除）、
`test_element_locator_views_split.py`（`backend/apps/element_locator` 已下线）、`test_example_integration.py`（模板示例）。
