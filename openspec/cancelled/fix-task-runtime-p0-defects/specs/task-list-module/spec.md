# task-list-module Delta

## ADDED Requirements

### Requirement: 清空任务与单任务删除同口径清理媒体

调试清空 MUST 与单任务删除同口径：删除任务记录的同时 MUST 清理这些任务的媒体文件（截图等磁盘产物），MUST NOT 只删表行而遗留孤儿文件。清空的路径、响应信封与删除范围口径 MUST 保持既有契约不变。

#### Scenario: 清空后媒体目录不遗留孤儿文件

- **WHEN** 存在带截图媒体的任务，用户触发调试清空
- **THEN** 任务记录被删除，且这些任务的媒体文件一并从磁盘清理

#### Scenario: 清空响应契约不变

- **WHEN** 用户触发调试清空
- **THEN** 响应仍为既有 `{status, data}` 信封与删除条数字段，前端无需改动