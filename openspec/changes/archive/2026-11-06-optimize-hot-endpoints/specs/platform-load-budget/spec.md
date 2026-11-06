## Purpose

约束平台高频接口的响应预算：设备状态不在请求线程里反复跑 ADB、运行中报告不重复全量构建、串口日志读取有界、列表计数一次聚合，避免页面打开被单点同步 I/O 拖慢。

## ADDED Requirements

### Requirement: 设备状态同步按时间窗节流

`GET /api/devices/` 与 `GET /api/devices/heartbeat/` MUST 复用 10 秒内的设备状态同步结果，MUST NOT 在每个请求里重复执行 ADB 子进程扫描；并发请求 SHALL 只触发一次真实扫描。`GET /api/devices/current/` 对同一设备的 ADB 探测 MUST 缓存 10 秒。响应字段与状态语义 MUST 保持不变。

#### Scenario: 连续列表请求只扫一次

- **WHEN** 10 秒内连续请求两次设备列表
- **THEN** 第二次不执行 ADB 扫描，直接返回缓存结果
- **AND** 两次响应的设备字段一致

#### Scenario: 缓存过期后重新同步

- **WHEN** 距上次同步超过 10 秒再次请求
- **THEN** 执行一次新的 ADB 扫描
- **AND** 扫描结果同时供心跳接口复用

#### Scenario: 当前设备探测有缓存

- **WHEN** 10 秒内重复请求 `/api/devices/current/`
- **THEN** 只有第一次连接设备读取分辨率与前台应用

### Requirement: 报告接口有上限与短缓存

运行中任务的 `GET /api/tasks/{id}/report/` MUST 使用不超过 2 秒的短缓存，MUST NOT 在多个查看者的同一事件序号上重复构建；终态任务沿用 600 秒缓存与 ETag。`GET /api/reports/` MUST NOT 联表读取智能体大字段，扫描上限 MUST NOT 超过 1000 条、返回上限 MUST NOT 超过 500 条。

#### Scenario: 运行中报告短缓存

- **WHEN** 两个查看者在 2 秒内请求同一运行中任务的报告
- **THEN** 只构建一次报告
- **AND** 事件继续增长时以新的最大序号取新缓存键

#### Scenario: 报告列表有界

- **WHEN** 请求报告列表且任务超过 1000 条
- **THEN** 最多扫描 1000 条、返回 500 条
- **AND** 响应不包含智能体头像或线路配置大字段

### Requirement: 串口日志读取有界且不叠加

串口日志自动刷新 MUST 在上一轮未返回时跳过本轮，默认读取行数 MUST NOT 超过 500。GET 接口 MUST NOT 每次请求都执行端口监听对齐，MUST 以不超过 10 秒的间隔节流。

#### Scenario: 慢请求不叠加

- **WHEN** 自动刷新上一轮尚未返回
- **THEN** 本轮跳过
- **AND** 上一轮返回后按 5 秒节奏继续

#### Scenario: 读接口不反复启停监听

- **WHEN** 连续请求端口列表或日志行
- **THEN** 10 秒内只执行一次监听对齐
- **AND** 响应内容不变

### Requirement: 列表计数一次聚合

项目列表与原型列表 MUST 用一次 `annotate(Count)` 产出每个条目的用例数/文档数，MUST NOT 对每一行单独执行 `COUNT`。

#### Scenario: 项目列表查询数恒定

- **WHEN** 请求项目列表，返回 P 个项目
- **THEN** 查询条数与 P 无关
- **AND** 每个项目的 `case_count` 与逐个计数一致

#### Scenario: 原型列表查询数恒定

- **WHEN** 请求原型列表，返回 P 个原型
- **THEN** 查询条数与 P 无关
- **AND** `doc_count` 只统计支持类型
