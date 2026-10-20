## REMOVED Requirements

### Requirement: 装配台提供平台工具调试入口

**Reason**: AI 工具箱整体下线，装配台与其中的平台工具卡不再存在。
**Migration**: 无替代入口；平台工具调试能力随工具箱一并退役。

### Requirement: 调试页按 schema 收集入参并展示结果

**Reason**: 调试页随工具箱删除。
**Migration**: 无。

### Requirement: 登录用户可读取工具入参 schema

**Reason**: 该端点只服务调试页，随调试页删除。
**Migration**: 无。

### Requirement: 只读工具任意登录用户可调用

**Reason**: 调试调用端点随工具箱删除。
**Migration**: 无。

### Requirement: 写工具仅超级管理员可调用且须确认

**Reason**: 调试调用端点随工具箱删除，不再存在写工具调试入口。
**Migration**: 无。

### Requirement: 设备参数候选限于可见、在线且未被占用的设备

**Reason**: 候选设备清单只服务调试表单，随调试页删除。
**Migration**: 无。

### Requirement: 调试调用失败按成因区分状态码

**Reason**: 调试调用端点已删除。
**Migration**: 无。

### Requirement: 调试失败展示服务端可读错误

**Reason**: 调试页已删除。
**Migration**: 无。
