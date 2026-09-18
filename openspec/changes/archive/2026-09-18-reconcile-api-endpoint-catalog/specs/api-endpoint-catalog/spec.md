## Purpose

`tools/seed_api_endpoints.py` 把平台自身的 API 描述为接口资产（元素定位模块的 `ApiGroup` / `ApiEndpoint`），
供接口测试选用。本能力规定：目录中的每个条目 MUST 指向路由表中真实存在的端点，
且该一致性由默认测试守护 —— 使"路由删了、目录没跟着删"表现为测试失败，而不是留下无法执行的资产。

## ADDED Requirements

### Requirement: 端点资产目录与路由表一致

目录（`tools/seed_api_endpoints.py`）中的每个端点条目 SHALL 指向路由表中存在的路径；
条目的 HTTP 方法 SHALL 是该路径已注册的方法之一。

目录 SHALL NOT 保留指向已不存在端点的条目。
删空的分组与目录（`create_group` / `create_folder`）SHALL 一并移除，不留空壳。

该一致性 SHALL 由 `tests/graybox/unit` 下的默认单元测试断言，MUST NOT 依赖运行中的服务。

#### Scenario: 目录中的每个路径都能命中路由

- **WHEN** 解析目录中的全部端点条目，并对其路径调用 `django.urls.resolve()`
- **THEN** 每条都命中视图，不出现 `Resolver404`

#### Scenario: 目录中不存在指向已删端点的条目

- **WHEN** 后端删除或改名某个路由，而目录未同步
- **THEN** 守护失败并列出该条目的路径与来源文件
- **AND** 修复方式是把该条目改名到新路径，或删除该条目

#### Scenario: 不保留空分组

- **WHEN** 某个分组或目录下的条目全部被移除
- **THEN** 该分组/目录的声明也被移除，不留下无条目的空壳

#### Scenario: 目录规模下限

- **WHEN** 守护扫描目录得到的条目数量低于登记下限
- **THEN** 守护失败并提示检查解析规则，而不是因为"目录变干净了"而通过
