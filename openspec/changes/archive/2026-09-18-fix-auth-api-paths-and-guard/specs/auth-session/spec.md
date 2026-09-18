## ADDED Requirements

### Requirement: 认证端点显式声明鉴权姿态

`apps/accounts` 的每个 APIView SHALL 满足：`permission_classes` 含 `AllowAny`
**当且仅当** `authentication_classes` 为空列表。公开端点因此必须同时声明「允许任何人」与「不做 DRF 鉴权」；
需要身份的端点 MUST NOT 出现二者只成立其一的状态。

该不变量 SHALL 由测试断言，以防止公开端点误继承鉴权类、或受保护端点被误开放。

#### Scenario: 公开端点两者成对

- **WHEN** 检查 `login` / `register` / `refresh` 三个端点
- **THEN** `permission_classes` 为 `AllowAny`
- **AND** `authentication_classes` 为空列表

#### Scenario: 受保护端点两者成对

- **WHEN** 检查 `logout` / `me` 两个端点
- **THEN** `permission_classes` 不含 `AllowAny`
- **AND** `authentication_classes` 非空（沿用 `REST_FRAMEWORK` 默认的 `shared.auth.drf_auth.JWTAuthentication`）

#### Scenario: 覆盖认证模块全部端点

- **WHEN** 遍历 `apps/accounts` 中的全部 APIView
- **THEN** 每个都满足上述不变量，没有一个落在「仅 AllowAny」或「仅空鉴权类」的中间态
