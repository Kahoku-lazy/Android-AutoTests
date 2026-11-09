## ADDED Requirements

### Requirement: 默认智能体随迁移种子化
平台 MUST 在数据库迁移执行时种下默认的**设备执行**智能体（`task_kind=device_control`），使任何全新环境在不依赖任何机器历史数据的前提下具备设备执行能力。种子 MUST 幂等：库中已存在任意设备执行智能体时 MUST NOT 新增记录。

#### Scenario: 全新数据库迁移后具备两类默认智能体
- **WHEN** 在一个空数据库上按顺序执行全部迁移
- **THEN** 库中同时存在设备执行与用例编写两个默认智能体
- **AND** 两者的 `task_kind` 分别为 `device_control` 与 `case_authoring`

#### Scenario: 已有设备执行智能体的库不重复种子
- **WHEN** 库中已存在任意 `task_kind=device_control` 的智能体
- **THEN** 迁移 MUST NOT 新增设备执行智能体
- **AND** 既有智能体的名称、归属与配置 MUST 保持不变

#### Scenario: 迁移重放不产生重复记录
- **WHEN** 种子迁移被重复执行
- **THEN** 设备执行智能体的数量保持不变

### Requirement: 无主智能体视为平台共享
`owner_id` 为空的智能体 MUST 对所有已登录用户可见并可用于提交任务，使种子结果不依赖「迁移执行时是否已存在超级管理员」。写权限 MUST 保持原状：仅超级管理员可创建、修改、删除智能体。

#### Scenario: 普通用户可见无主智能体
- **WHEN** 非超级管理员请求智能体列表
- **THEN** 响应 MUST 包含 `owner_id` 为空的智能体

#### Scenario: 普通用户可在无主智能体上提交任务
- **WHEN** 非超级管理员使用无主智能体提交任务
- **THEN** 系统 MUST 允许提交，不得判为不可见或返回 403

#### Scenario: 无主不放开写权限
- **WHEN** 非超级管理员请求修改该无主智能体
- **THEN** 系统 MUST 返回 403 且不修改记录

### Requirement: 历史无主智能体回填归属
迁移 MUST 把 `owner_id` 为空的智能体回填为「执行迁移时已存在的第一个超级管理员」，并 MUST NOT 修改名称、`task_kind`、`route_configs` 等其他字段；库中不存在超级管理员时 MUST 保持为空并交由「无主即共享」规则兜底。

#### Scenario: 存在超级管理员时回填归属
- **WHEN** 执行迁移时库中已有超级管理员且存在无主智能体
- **THEN** 这些智能体的 `owner_id` MUST 变为该超级管理员的 id
- **AND** 其他字段 MUST 保持不变

#### Scenario: 无超级管理员时不阻塞迁移
- **WHEN** 执行迁移时库中尚无任何超级管理员
- **THEN** 迁移 MUST 正常完成
- **AND** 无主智能体 MUST 仍对全部登录用户可见可用
