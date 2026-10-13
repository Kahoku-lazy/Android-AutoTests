## 1. 配置与工具选择

- [x] 1.1 `ModelConfig` 只保留连接字段；`CreateModel` 分 DeepSeek / OpenAI / DashScope 创建。验证：未知 provider 抛 `ValueError`；DashScope 空 `base_url` 不传入地址。**验证结果**：分发与空地址行为已用替身客户端核对。
- [x] 1.2 新增 `RoleConfig`，`BaseRole` 只接收模型配置和角色配置，并用其中的名称、提示词、工具包、ReAct、上下文创建 `Agent`。验证：装配出的 `Agent` 参数与 `RoleConfig` 一致。**验证结果**：已用替身 `Agent` 核对名称、提示词、工具包、`max_iters`、`max_image_num`。
- [x] 1.3 `tools_config.py` 按 `EXECUTOR_TOOL_NAMES` 选择并包装 `EXECUTOR_TOOLKITS`。验证：9 个名字得到 `Toolkit`；未知名字报错并列出可选名。**验证结果**：导入后为 9 个名字的 `Toolkit`，`nope` 触发 `ValueError`。

## 2. 中断

- [x] 2.1 `BaseRole.interrupt`：运行中取消当前回复任务；未在运行时发送 `UserInterruptEvent`。验证：运行中的 `reply` 变为 `CancelledError` 且不再发送中断事件；空闲时 `reply_stream` 收到 `UserInterruptEvent`。**验证结果**：两条路径均已用替身智能体核对；`ruff check engines/agents/role/base.py` 通过。
