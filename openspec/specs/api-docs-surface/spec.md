# api-docs-surface Specification

## Purpose
平台对外 API 文档面的行为契约：定义文档由哪些 URL 提供、内容来自何处、中文说明是否完整，以及在无外网环境下是否仍可阅读 —— 取代已废弃的手写文档副本。
## Requirements
### Requirement: 文档面 URL 收敛为 schema 与 swagger

平台 SHALL 仅通过 `/api/schema/`（OpenAPI 3.0 文档）与 `/api/swagger/`（Swagger UI 页面）对外提供 API 文档；SHALL NOT 再提供 `/api/docs` 与 `/api/docs.html` 两个手写文档端点，且不保留跳转。两个保留端点 SHALL 保持免 JWT 公开可访问（沿用既有「有意公开」裁定）。

#### Scenario: 已删除的文档路径不再返回文档
- **WHEN** 请求 `/api/docs` 或 `/api/docs.html`
- **THEN** 不返回任何文档内容：未携带 JWT 时为 401（网关拦截），携带有效 JWT 时为 404（无路由）

#### Scenario: 保留的文档端点保持公开可达
- **WHEN** 未携带任何凭据请求 `/api/schema/` 与 `/api/swagger/`
- **THEN** 两者均返回 200，且响应分别为 OpenAPI 文档与 Swagger UI 页面

### Requirement: 文档内容单一来源

文档内容 SHALL 全部由 drf-spectacular 从代码生成（视图 docstring 与 `@extend_schema` 标注）；平台 SHALL NOT 维护任何手写的端点清单副本或第二套文档数据源。

#### Scenario: schema 生成无错误
- **WHEN** 运行 `python manage.py spectacular --validate`
- **THEN** 报告中 Errors 为 0（Warnings 允许登记后保留）

#### Scenario: 手写副本已清除
- **WHEN** 检索仓库
- **THEN** 不存在 `config/api_docs.py`，也不存在手写端点清单常量（原 `ENDPOINTS`）及其看守测试

### Requirement: 中文说明完整

`/api/schema/` 中每个 operation SHALL 带有非空的中文 description 或 summary，每个 tag SHALL 带有中文说明，以保证删除手写文档后不丢失中文可读性。

#### Scenario: 端点说明齐全
- **WHEN** 解析 `/api/schema/` 的全部 operation
- **THEN** 每个 operation 的 description 或 summary 均非空

#### Scenario: 分组说明可读
- **WHEN** 打开 `/api/swagger/`
- **THEN** 每个分组（tag）显示中文说明，而不是仅有英文标识

### Requirement: 文档面离线可用

`/api/swagger/` SHALL 在无外网（无法访问 CDN 与外部字体服务）的环境下完整渲染；该页面引用的样式与脚本 SHALL 全部由本服务同源提供，页面 HTML 中 SHALL NOT 出现第三方域名的资源引用。

#### Scenario: 页面不含第三方外链
- **WHEN** 请求 `/api/swagger/`
- **THEN** 返回的 HTML 中不存在指向第三方域名（CDN、Google Fonts 等）的 script/link 引用

#### Scenario: 引用资产同源可取
- **WHEN** 逐条请求页面引用的每个静态资源 URL
- **THEN** 全部返回 200，页面在断网环境下仍可渲染出接口列表
