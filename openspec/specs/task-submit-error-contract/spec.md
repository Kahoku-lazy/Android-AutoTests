# task-submit-error-contract Specification

## Purpose
约束提交任务接口在服务端落盘失败时的失败响应：调用方必须拿到 `{status:false, message}` 信封与可执行的排查方向，而不是 Django 的 HTML 500 页或前端兜底的通用文案。

## Requirements

### Requirement: 附件写入失败必须返回可读原因

服务端把任务配置附件写入上传目录失败时，`POST /api/tasks/submit/` MUST 返回 HTTP 500 与 `{status: false, message}` 信封。`message` MUST 说明失败发生在「任务配置文件写入」这一步，MUST 给出可执行的排查方向（运行账号对上传目录的写权限），并 MAY 附带操作系统的错误原因（如 `Permission denied`）。`message` MUST NOT 为空，MUST NOT 只给「服务暂时异常」一类不含定位信息的通用文案。

响应的 `Content-Type` MUST 是 JSON（`application/json`），MUST NOT 是 `text/html`。完整异常堆栈 MUST 记入后端日志，供服务端排障。

#### Scenario: 上传目录不可写时返回信封而不是 HTML 页

- **WHEN** 提交一份合法的里程碑 YAML，而上传目录对当前运行账号不可写（写文件抛 `PermissionError`）
- **THEN** 响应状态码为 500
- **AND** `Content-Type` 是 `application/json`
- **AND** 响应体为 `{status: false, message: "..."}`，`message` 含「写入失败」与「写权限」字样

#### Scenario: 平台用例来源同样返回可读原因

- **WHEN** 用例来源为平台用例、所选用例已编译成里程碑，但保存这份配置附件时写盘失败
- **THEN** 响应仍是 500 + `{status: false, message}` 信封
- **AND** `message` 与里程碑来源的失败文案同一口径

### Requirement: 写入失败不留下任务

配置附件写入失败时，该次提交 MUST NOT 在库中留下任务行，也 MUST NOT 留下附件记录。任务创建、附件落盘与附件记录写入 MUST 同属一个原子操作：任一步失败，整次提交按原子性回滚。

#### Scenario: 失败后任务表不新增行

- **WHEN** 一次提交因上传目录不可写而失败
- **THEN** 任务表中不出现这条任务
- **AND** 该任务的附件表中没有对应记录

### Requirement: 成功与既有失败口径不变

本次约束 MUST NOT 改变提交成功时的行为：成功仍返回 `{status: true, data}`，载荷与状态码不变。既有的参数校验失败（缺少工作流、未选设备、未选用例、工作流未发布、里程碑格式不合法等）MUST 继续返回原有状态码（400/404 等）与既有可读原因，MUST NOT 被替换为「写入失败」文案。

#### Scenario: 合法提交仍然成功

- **WHEN** 上传目录可写，提交一份合法里程碑 YAML 与一台设备
- **THEN** 响应仍为 `{status: true, data: {id, status}}`
- **AND** 任务按既有口径创建并下发

#### Scenario: 参数错误不被误判为存储失败

- **WHEN** 提交缺少工作流编号，或里程碑 YAML 格式不合法
- **THEN** 响应仍是原有的 400 与原有原因文案
- **AND** 不出现「任务配置文件写入失败」
