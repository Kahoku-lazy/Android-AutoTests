## Why

测试用例编写助手走 govee 网关调用 `grok-4.7` 时，第一轮就被 400 拒绝：`Only message of role user can have a name.` 同一网关下的 `deepseek-flash` 接受 system 消息上的 `name`。两条请求的厂商、地址和协议都相同，不能靠这些字段区分上游。

## What Changes

- govee 创建的 OpenAI 兼容模型，在发出请求前去掉 `system` 与 `assistant` 消息上的 `name` 键。
- 保留 `user.name` 与 `tool.name`。
- 不按模型名前缀分支，不改 Agent 名字，不改提示词正文。
- 直接走 `provider=deepseek` / `dashscope` 的请求保持现状。

## 关联文档

无关联 PRD。这是线上 400 的兼容修复，范围只限 govee 消息格式化。

## Capabilities

### New Capabilities

- `govee-message-name`: govee 网关发出的 OpenAI 兼容消息，非 user、非 tool 角色不携带 `name`。

### Modified Capabilities

## Impact

- 代码：`engines/ae_harness/agents/models.py`。
- 测试：`tests/engines/ae_harness/unit/` 增加格式化断言，不发真实网关请求。
- 不影响 SOP 流程、提示词文件和运营配置表。
