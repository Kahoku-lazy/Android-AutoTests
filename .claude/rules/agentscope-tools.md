# AgentScope Tools — Android-AutoTests

> 开发新 AgentScope 功能前，先阅读 [AgentScope 2.0.3 文档](https://docs.agentscope.io/versions/2.0.3/zh)。

## 核心模式

Agent 本身不直接访问数据库，所有平台操作必经 Tool 层。Tool 通过 `run_sync()` 异步桥接调用 Django ORM/API（8s 超时）。

## 获取 Tool 列表

Read `agentscope_service/tools/factory.py` → `_ALL_BUSINESS_TOOLS`。每个 Tool 的 `name`/`description`/`input_schema` 在其类定义中。

## 新增 Tool

在 `agentscope_service/tools/{domain}_tools.py` 创建 `ToolBase` 子类 → 在 `factory.py` 注册。

## 约束

| 规则 | 说明 |
|------|------|
| 必须继承 `ToolBase` | 框架通过基类发现和注册 |
| 读 Tool 设 `is_read_only=True` | 框架借此判断是否需要用户确认 |
| 写 Tool 必须走 Django `api.py` | 禁止 Tool 内直接 ORM 写入 |
| 返回值用 `ToolChunk` | 包装 `TextBlock` 或 `HintBlock` |
