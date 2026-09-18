## ADDED Requirements

### Requirement: 无引用样式文件不得留在源码树
源码树 SHALL NOT 保留没有任何引用的样式文件（既无路径引用、也无变量消费）。识别出的死样式文件 MUST 移出源码树或删除，并记录恢复方式。

#### Scenario: 死样式文件的处置
- **WHEN** 某样式文件在全仓既无 `@import` / `src` 路径引用，其声明的自定义属性也无任何消费方
- **THEN** 该文件 MUST 移出 `frontend/src`（或删除），且处置方式 MUST 可恢复

### Requirement: 共享样式目录命名唯一
跨模块共享样式 SHALL 只位于 `shared/styles/` 与 `shared/components/`；其它目录 SHALL NOT 复用 `shared` 这一级命名空间。

#### Scenario: 视图层局部样式不占用 shared 命名
- **WHEN** 视图层需要归集自身的局部样式
- **THEN** 其目录 MUST NOT 命名为 `shared`（如改为 `views/styles/`），避免与平台 `shared/` 混淆

#### Scenario: 目录改名后引用同步
- **WHEN** 归集目录改名
- **THEN** 所有引用该目录的 `@import` / `src` 路径 MUST 同步更新，且旧路径命中 MUST 为 0