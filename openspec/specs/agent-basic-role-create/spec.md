# agent-basic-role-create Specification

## Purpose

定义一个可运行角色的创建边界：名称、提示词正文、连接参数三要素，经 `create_agent` 得到独立智能体。工具在创建之后由调用方挂载。

## Requirements

### Requirement: 基本角色由调用方三要素创建

一个可运行角色 MUST 由三样东西组成：调用方传入的名称、系统提示词正文，以及经 `create_model` 创建的聊天模型。`create_agent` MUST NOT 接收工具、记忆、能力型中间件、角色表或编排参数。观测、重试、预算与取消 MUST 由调用方显式传入，默认一个都不挂。

#### Scenario: 三要素创建

- **WHEN** 调用方传入名称、非空正文和合法连接参数
- **THEN** 返回的智能体只含这三样，工具包为空

#### Scenario: 不传短名

- **WHEN** 调用方尝试用模型短名创建
- **THEN** 没有可接受短名的参数，创建无法完成

### Requirement: 工具在创建之后挂载

工具 MUST NOT 作为 `create_agent` 的参数。调用方 MUST 在拿到智能体后自行挂载。验收侧 MUST 只挂勾选与只读目录的交集。

#### Scenario: 创建时不带工具

- **WHEN** 刚从 `create_agent` 拿到智能体
- **THEN** 其工具包为空

#### Scenario: 验收勾选含写操作

- **WHEN** 装配验收者，且勾选里有写操作工具
- **THEN** 写操作工具不在验收者的工具集里

### Requirement: 提示词只接受正文

`create_agent` 的系统提示词参数 MUST 按正文使用。它 MUST NOT 打开文件，MUST NOT 把特定字符串当作提示词文件名。业务代码 MUST NOT 在 View 内写死一段角色提示词来绕过调用方配置。

#### Scenario: 旧文件名原样保留

- **WHEN** 传入的正文恰好是 `UI_EXECUTOR_PROMPT`
- **THEN** 智能体的系统提示词就是这串文字，不读取 `prompts/` 下的文件
