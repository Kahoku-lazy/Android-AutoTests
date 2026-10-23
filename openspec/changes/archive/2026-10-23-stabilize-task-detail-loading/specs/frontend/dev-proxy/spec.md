## Purpose

让开发期浏览器对 `/api`、`/media` 的请求在后端重启或不可用时得到可诊断的失败语义，而不是被当成业务接口返回的 500。

## ADDED Requirements

### Requirement: 开发代理的上游不可用语义

系统 SHALL 在 Vite 开发代理把 `/api` 与 `/media` 请求转发到 Django 后端时拦截与上游建立连接的失败（连接被拒绝、连接被重置）。此时 MUST 返回 HTTP `503` 与 JSON `{status: false, message}`，`message` MUST 为中文可读原因。系统 MUST NOT 用 `500` 表示代理连接失败。后端自身返回的任意 5xx MUST 原样透传状态码与响应体。代理 MUST 在响应已开始写出时不再写第二次状态码与响应体。

#### Scenario: 后端未监听时返回 503

- **WHEN** 后端未监听 8766，浏览器请求 `/api/tasks/141/report/`
- **THEN** 浏览器收到 503 与 `{status: false, message}`，控制台不再出现 `Request failed with status code 500`

#### Scenario: 后端自身的 500 原样透传

- **WHEN** 后端对某个 `/api/*` 请求返回 500 与既有错误体
- **THEN** 浏览器收到同样的 500 与响应体，不被改写成 503

#### Scenario: 响应已开始时只记录不重写

- **WHEN** 上游在响应头已经发送之后断开连接
- **THEN** 代理不再写入第二个状态码或响应体，只记录错误
