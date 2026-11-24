# tests · 集成测试与接口测试

> 归属模块：`tests/<模块>/integration/`、`tests/api_kit/`、`tests/api/` ｜ 类型：模块功能开发说明
> 代码真相源：`tests/pytest.ini`、`tests/api_kit/loader.py`、`tests/api_kit/schemas.py`、`tests/api/conftest.py`、`tests/api/case/*.yaml`
> 上级约束：根 `AGENTS.md` ｜ 模块索引：`tests/AGENTS.md`

## 集成测试

> 运行指令： `python -m pytest tests/<模块>/integration -v`

1. 集成测试放 `tests/<模块>/integration/`，文件以 `test_` 开头。

## 接口测试

> 运行指令： `python -m pytest tests/<模块>/api -v`（共享设施：`tests/api_kit/`；夹具与 YAML 用例：`tests/api/`）

1. 接口脚本放 `tests/<模块>/api/`；共享加载器与 JSONSchema 在 `tests/api_kit/`。
2. 接口测试使用 Jsonschema 断言响应，YAML 用例放 `tests/api/case/`（契约测试硬编码了该路径，不随脚本迁移）。
3. YAML 用例要有测试标题、测试点。

## 接口测试脚本与模块映射

> 模块 marker 见 `tests/pytest.ini`。

| 模块 | 测试脚本 | YAML 用例 | 覆盖功能 |
|---|---|---|---|
| 登录鉴权 | `tests/auth/api/` | case/login.yaml、register.yaml、refresh.yaml、logout.yaml、me.yaml | 登录 / 注册 / 刷新 / 登出 / 当前用户 / 并发注册 |
| 设备管理 | `tests/device/api/test_devices.py` | case/devices.yaml | 设备列表 / 锁定 / 连接 / 断开 / 释放 / 心跳 / 当前设备 |
| 设备检查器 | `tests/device/api/test_inspector.py` | case/inspector.yaml | 快照抓取 / 列表 / 删除 / 保存到元素定位 |
| 串口日志 | `tests/serial_log/api/test_serial_log_api.py` | — | 端口列表 / 开关 / 行读取 / 关键词 |
| 仪表盘 | `tests/dashboard/api/test_dashboard_agent_usage.py` | — | 智能体用量 |
| 任务清单 | `tests/task/api/` | — | 提交 / 统计 / 事件流 / 媒体 / 报告 / 取消 |
| 用例管理 | `tests/case/api/` | — | 用例定义 / YAML 导入 |
| bug 单 | `tests/bug_ticket/api/test_bug_tickets.py` | — | 列表 / 详情 / 状态 |
