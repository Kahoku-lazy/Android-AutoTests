## Context

- 中间件的原始动机：`CommonMiddleware` 的 `APPEND_SLASH` 会对无斜杠请求发 301，部分客户端重定向时丢失
  `Authorization` 头 → JWT 中间件误报 401（真机发现 #1）。故当时直接补斜杠、消掉 301。
- Django 没有"去斜杠"的对应机制（`APPEND_SLASH` 只追加不删除），所以反方向一直是 404。
- 平台路径约定不统一（见 proposal 的实测表），调用方无法从文档推断统一写法。
- 该中间件此前**零测试**：`tests/` 下搜 `NormalizeTrailingSlash` 无命中。

## Goals / Non-Goals

**Goals**：让调用方不必关心路由定义用的是哪种写法；同时不改变任何路径定义与 API 契约。

**Non-Goals**：统一各 App 的路径约定（会动契约、schema、文档、前端）；改 `APPEND_SLASH`。

## Decisions

**D1：改中间件，而不是统一路径约定。**

| 方案 | 结论 | 理由 |
|---|---|---|
| 把 `accounts` 等改为带斜杠 | ❌ | 改动 OpenAPI schema、接口文档、前端调用点、seed 数据；且平台仍有其他混用处，治标不治本 |
| 中间件双向容错（**采用**） | ✅ | 一处修复覆盖全部 App；零契约改动；正是网关「规范化」职责所在 |

**D2：只在原路径解析失败时才改写。**

这条是安全性关键：`element_locator` 同时注册了 `batch-move` 与 `batch-move/`。
若无条件去斜杠，会把本该命中 A 路由的请求改写到 B 路由 —— 静默改变语义。
先判 `resolver.resolve(path)` 成功即返回，可完全避免。

**D3：只写 `path_info`，不动 `request.path`。**

与既有实现保持一致。鉴权白名单（`gateway.middleware._is_public`）按前缀匹配，
`/api/auth/login/` 与 `/api/auth/login` 同属公开前缀，故不影响鉴权判定。

## Risks / Trade-offs

- [同一资源两种写法并存] 由 D2 兜住：原路径可解析即不改写，语义不会被静默改写
- [缓存/日志出现两种 path] 改写发生在解析层，日志与缓存键看到的仍是原始 path_info；属既有行为
- [可能掩盖调用方的错误] 这是有意的权衡：本平台约定不统一，容错比强制更实用；
  若要强制统一写法，应作为独立变更去收敛各 App 的 `urls.py`

## Migration Plan

无需迁移。回滚 = 还原 `gateway/normalize_slash.py`。

## Open Questions

1. 是否值得单独立一个变更**统一各 App 的路径约定**（并同步 schema、接口文档与前端）？
2. `boundary-check` / `gen_arch_stats` 是否应把「同 App 内路径约定混用」纳入扫描？
