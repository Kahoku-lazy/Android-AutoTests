# tests · 灰盒层（接口 + 集成 + 落库校验）

> 归属模块：`tests/<模块>/api/`、`tests/<模块>/integration/`、`tests/api_kit/`、`tests/api/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/pytest.ini`、`tests/api_kit/loader.py`、`tests/api_kit/schemas.py`、`tests/api/conftest.py`、`tests/api/case/*.yaml`
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## 灰盒是什么口径

以**功能**为单位：从一个真实入口把功能走完，断言"调用方 / 用户能观察到的结果"。
不 mock 被测模块内部实现，不按函数、分支、边界值拆用例（那是已退役的单元层，见 `tests/AGENTS.md`）。

- 从 HTTP 进 → 放 `tests/<模块>/api/`（`pytest.mark.api`）
- 从服务层 / ORM 进（多模块协作、序列化器、状态机）→ 放 `tests/<模块>/integration/`（`pytest.mark.integration`）

两处的区别只是**入口**，颗粒度一致：一个功能一条用例。

> 运行指令： `python -m pytest tests/<模块>/api -v` ｜ `python -m pytest tests/<模块>/integration -v`

## 颗粒度（与 `tests/AGENTS.md` 对齐）

- ✅ `test_platform_assistant_create_and_delete`：新建 → 列表出现 → 删除 → 列表消失 → 库里无残留。
- ✅ `test_dashboard_stats_match_records`：造几条账本记录 → 拉接口 → 断言聚合数字与记录一致。
- ❌ `test_serializer_length_limit`、`test_view_delete_returns_204`、`test_model_str`：按函数拆，属单元层。

需求方点名的分支（例如注册并发、禁用账号）可以单独成用例，因为它们本身就是功能。

## 落库校验（前端改完，库里到底变没变）

写类功能必须在**同一条用例末尾**用 ORM 读回。接口返回 200 不等于数据进了库 —— 事务回滚、漏 `save()`、
只写缓存都能让响应体看着正常。

```python
pytestmark = [pytest.mark.django_db, pytest.mark.api]

def test_platform_assistant_create_and_delete(auth_session, base_url):
    created = auth_session.post(f"{base_url}/api/ai/assistants/", json={...})
    assert created.status_code == 201
    assistant_id = created.json()["data"]["id"]
    assert AIAssistant.objects.filter(id=assistant_id).exists()        # 落库校验

    deleted = auth_session.delete(f"{base_url}/api/ai/assistants/{assistant_id}/")
    assert deleted.status_code == 204
    assert not AIAssistant.objects.filter(id=assistant_id).exists()    # 删除也落到库
```

模型名与路径以 `backend/apps/<模块>/models.py`、`urls.py` 为准；上面只是形状示例。

## 共享设施

1. 接口脚本放 `tests/<模块>/api/`；共享加载器与 JSONSchema 在 `tests/api_kit/`。
2. 接口测试使用 Jsonschema 断言响应，YAML 用例放 `tests/api/case/`（契约守护硬编码了该路径，不随脚本迁移）。
3. YAML 用例要有测试标题、测试点。

## 灰盒脚本与模块映射

> 模块 marker 见 `tests/pytest.ini`。

| 模块 | 测试脚本 | YAML 用例 | 覆盖功能 |
|---|---|---|---|
| 登录鉴权 | `tests/auth/api/` | case/login.yaml、register.yaml、refresh.yaml、logout.yaml、me.yaml | 登录 / 注册 / 刷新 / 登出 / 当前用户 / 并发注册 / 禁用账号 |
| 设备管理 | `tests/device/api/test_devices.py`、`tests/device/integration/` | case/devices.yaml | 设备列表 / 锁定 / 连接 / 断开 / 释放 / 心跳 / 注册表 / 状态机 |
| 串口日志 | `tests/serial_log/api/`、`tests/serial_log/integration/` | — | 端口开关 / 行读取 / 关键词增删改查 / 自定义端口 |
| 仪表盘 | `tests/dashboard/api/test_dashboard_agent_usage.py` | — | 智能体用量 |
| 平台助手 | `tests/ai_assistant/api/` | — | 助手 / 模型配置 / 角色 / SOP 工作流 / 评估 / 发布 |
| 任务清单 | `tests/task/api/` | — | 提交 SOP / 媒体存储 / 路径 |
| 用例管理 | `tests/case/api/test_case_definitions_api.py` | — | 用例定义 / YAML 导入 |
| 知识库 | `tests/knowledge_search/{api,integration}/` | — | 检索 / 评估运行 / 路径变更 |
| bug 单 | `tests/bug_ticket/api/test_bug_tickets.py` | — | 列表 / 详情 / 状态 |
| 运维控制台 | `tests/ops_console/api/` | — | 授权 / 批量 / 改密 / 启停 / 禁删 |
| 测试报告 | `tests/report/integration/test_report_envelope.py` | — | 报告信封 |
