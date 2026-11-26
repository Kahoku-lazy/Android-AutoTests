# api-path-convention delta

## REMOVED Requirements

### Requirement: 前端与测试调用面遵循唯一写法

**Reason**: 该要求的两张扫描面都以用例为载体——`tests/` 的 HTTP 调用字面量与 `tests/api/case/*.yaml` 的
`path:` 字段；2026-11-24 用例层迁至 `temps/tests-archive/` 冷备后，仓库内不再有可扫描的测试调用面。
保留原要求会让 `tests/arch/unit` 的守护对空集合断言，或被迫去扫一个被 `.gitignore` 声明的目录。

**Migration**: 前端 API 层这一面由本变更新增的「前端调用面遵循唯一写法」承接（同一守护
`tests/arch/unit/test_api_path_callers.py`，只留 `frontend/src` 面）；测试调用面在系统化测试就位、
用例重新入仓时按新用例目录重新纳入扫描，届时再以 delta 恢复。

## ADDED Requirements

### Requirement: 前端调用面遵循唯一写法

`frontend/src` 中作为 HTTP 调用参数出现的 `/api/` 路径字面量 SHALL 以 `/` 结尾，且 SHALL 能在 Django 路由表中
解析命中；仅指向前端自身路由的字面量（如 `/login`）不在本约束内。

该一致性 SHALL 由 `tests/arch/unit` 下的契约守护断言，MUST NOT 依赖运行中的前端或后端服务，
MUST NOT 依赖需要显式开启的环境变量或凭据。

故意使用无尾斜杠的负向用例 SHALL 登记在守护测试的显式例外清单中并注明理由。

#### Scenario: 前端 API 路径带尾斜杠

- **WHEN** 扫描 `frontend/src` 中作为 `.get`/`.post`/`.put`/`.patch`/`.delete(` 或 `fetch(` 首个参数出现的 `/` 开头字面量
- **THEN** 每一条都以 `/` 结尾（前端自身路由与显式例外除外）

#### Scenario: 前端路径命中路由表

- **WHEN** 把前端每条 `/api/` 路径字面量拼上 `baseURL=/api` 后交给 `django.urls.resolve()`
- **THEN** 每条都命中视图，不出现 `Resolver404`

#### Scenario: 负向用例显式登记

- **WHEN** 某守护用例需要断言「缺失尾斜杠返回 404」
- **THEN** 该路径出现在守护测试的显式例外清单中，并注明理由
