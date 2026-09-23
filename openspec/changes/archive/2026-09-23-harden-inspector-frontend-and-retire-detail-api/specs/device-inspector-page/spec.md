## MODIFIED Requirements

### Requirement: 请求失败如实呈现原因

检查器的每次请求失败 MUST 向用户呈现后端返回的可读原因（经共享错误净化 `formatApiError`），MUST NOT 用与该原因无关的通用文案顶替。「重试」入口 MUST 真的重新发起最近一次失败的那一个请求，MUST NOT 只清空提示。可重试来源 MUST 只有设备列表、快照列表、抓取与分层数据四类：快照回看一律消费分层端点（见 `device-inspector-snapshots`），MUST NOT 再把已退役的「快照详情」列为可重试来源。

#### Scenario: 抓取被占用时显示后端原因

- **WHEN** 选定设备正被执行引擎占用，用户点「获取」
- **THEN** 提示包含后端返回的占用原因（形如「设备正被执行引擎占用（runner-xxx），请等待执行完毕」）
- **AND** MUST NOT 只显示「获取失败」

#### Scenario: 保存冲突时显示后端原因

- **WHEN** 保存到元素定位时目标同级重名（HTTP 409）
- **THEN** 提示包含后端返回的冲突原因
- **AND** MUST NOT 只显示「保存失败」

#### Scenario: 重试重新发起请求

- **WHEN** 某次请求失败后用户点击错误条上的「重试」
- **THEN** 系统重新发起刚刚失败的那一个请求（设备列表 / 快照列表 / 抓取 / 分层数据之一）
- **AND** 请求成功后错误条消失

## ADDED Requirements

### Requirement: 检查器前端跨模块口径集中登记

媒体相对路径的展示 URL 拼接（相对路径 → `/media/{path}`，空路径 → 空串）与「设备是否被执行引擎占用」（`status` 为 `BUSY` 且 `occupied_by` 以执行引擎占用前缀开头）这两项口径 MUST 各由 `frontend/src/shared/` 下的唯一登记处提供。设备检查器、元素定位、AI 助手与设备管理 MUST 复用该登记处，MUST NOT 在模块内再复制路径字面量或占用前缀清单。执行引擎占用前缀清单 MUST 只有一处定义，设备管理页与设备检查器对同一台设备的占用判定 MUST 一致。

#### Scenario: 媒体 URL 字面量只有一处

- **WHEN** 扫描 `frontend/src` 中的 `/media/` 拼接字面量
- **THEN** 它只出现在共享登记处，各业务模块内不再出现 `/media/` 字面量

#### Scenario: 空路径不产出 URL

- **WHEN** 元素的缩略图路径为空字符串
- **THEN** 共享登记处返回空字符串，MUST NOT 产出指向站点根的 `/media/`

#### Scenario: 占用前缀清单只有一处

- **WHEN** 扫描 `frontend/src` 中的执行引擎占用前缀清单定义
- **THEN** 它只出现在共享登记处，设备管理与设备检查器都从该处引用

#### Scenario: 两处占用判定一致

- **WHEN** 同一台设备（`status` 为 `BUSY` 且 `occupied_by` 以执行引擎前缀开头）同时出现在设备管理页与检查器的设备下拉
- **THEN** 两处都判定为「被执行引擎占用」，检查器 MUST NOT 提供该设备
