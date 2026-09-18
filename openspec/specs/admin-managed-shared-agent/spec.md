# admin-managed-shared-agent Specification

## Purpose
TBD - created by archiving change admin-managed-shared-agent. Update Purpose after archive.
## Requirements
### Requirement: 超级管理员身份判定
平台 API MUST 能将 JWT 认证用户解析为平台真实用户，并 MUST 能判定其是否为超级管理员，供权限控制复用。

#### Scenario: 超级管理员访问 API
- **WHEN** 超级管理员携带有效 JWT 令牌访问受保护 API
- **THEN** 系统将其识别为超级管理员（`is_superuser` 为真）

#### Scenario: 普通用户访问 API
- **WHEN** 非超级管理员携带有效 JWT 令牌访问受保护 API
- **THEN** 系统将其识别为普通用户（`is_superuser` 为假）

### Requirement: 智能体配置仅超级管理员可写
系统 MUST 仅允许超级管理员创建、更新、删除智能体，以及导入工具箱项、查看完整 API Key。

#### Scenario: 普通用户创建智能体被拒
- **WHEN** 非超级管理员请求创建智能体
- **THEN** 系统返回 403 且不创建记录

#### Scenario: 普通用户修改智能体被拒
- **WHEN** 非超级管理员请求更新或删除智能体
- **THEN** 系统返回 403 且不修改记录

#### Scenario: 超级管理员配置智能体
- **WHEN** 超级管理员请求创建、更新或删除智能体
- **THEN** 系统允许执行该操作

### Requirement: 共享智能体对普通用户可见且可用
非超级管理员 SHALL 能查看超级管理员配置的智能体，并 MUST 能在其上创建和继续自己的对话。

#### Scenario: 普通用户查看共享智能体
- **WHEN** 非超级管理员请求智能体列表或详情
- **THEN** 系统返回超级管理员配置的共享智能体

#### Scenario: 普通用户在共享智能体上对话
- **WHEN** 非超级管理员在共享智能体上创建或继续对话
- **THEN** 系统允许该对话，且该对话归属于该用户

### Requirement: 共享智能体下数据隔离
在共享智能体对话中，工具调用 MUST 以发起对话的用户身份写库，SHALL NOT 以超级管理员身份跨用户写入。

#### Scenario: 普通用户经共享智能体写用例
- **WHEN** 非超级管理员在共享智能体对话中触发写操作（如保存用例）
- **THEN** 数据写入该用户名下，其他用户不可见该数据

### Requirement: 超级管理员对话审计
超级管理员 SHALL 能在 Django 后台查看所有用户的对话与消息记录，并 MUST 能按所属用户过滤或搜索。

#### Scenario: 超级管理员审计对话
- **WHEN** 超级管理员在 Django 后台打开对话或消息列表
- **THEN** 系统展示所有用户的记录，且可按所属用户过滤或搜索

