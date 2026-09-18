## Why

平台的 API 路径约定**不统一**，且根因是结构性的：**DRF router 默认生成带斜杠路径，手写 `path()` 通常不带**，
两条生成方式并存 —— 同一个 App 内也会混用（`element_locator` 10 个 router + 7 条手写无斜杠）。实测：

```
accounts          router 0 条 · 手写无斜杠 5 条        → 全部无斜杠
element_locator   router 10 条 · 手写无斜杠 7 条       → 同 App 内混用
dashboard         手写但带斜杠                          → 另一种写法
```

前一变更（`normalize-trailing-slash-both-ways`）用中间件**容忍**了这种不一致。本变更是相反的取舍：
**统一约定 + 关掉 301 + 删掉中间件**，把"网关替调用方兜底"换成"契约只有一种正确写法"。

理由：容忍使约定长期无法收敛（`Django` 的 `APPEND_SLASH=True` 是一条已知有害的路径 —— 301 会丢
`Authorization` 头、可能把 POST 降级为 GET、并被浏览器长期缓存）。与其同时维护"两种写法都对"和
"路由定义混乱"，不如把约定钉死。

## What Changes

- **统一路由约定为带斜杠**：`apps/*/urls.py` 的 **111 条**手写 `path()` 全部补 `/`（router 生成的已带）
- **关闭 301**：`config/settings.py` 增加 `APPEND_SLASH = False`
- **删除中间件**：移除 `gateway/normalize_slash.py` 与 `MIDDLEWARE` 中的对应项；其行为契约由规格移除
- **更新全部调用方**：前端 api 层、`tests/api/case/*.yaml`、`tools/seed_api_endpoints.py`（端点资产目录）
  中的路径串补斜杠
- **同步文档与 schema**：`dev_docs` 中的路径引用、OpenAPI schema、接口文档
- 新增/改写测试：断言**严格语义** —— 缺失尾斜杠返回 404（替代原中间件的双向容错用例）

**Non-goals**：
- 不改路由的**层级/命名**（如 `/api/elements/pages` 仍是该路径，只是补上尾斜杠）
- 不改 DRF router 的 `trailing_slash` 配置（默认已是 True）
- 不引入 308/307 重定向作为过渡（会保留"两种写法"的幻觉）

## Capabilities

### New Capabilities

- `api-path-convention`：`/api/` 路由的唯一写法（全部带尾斜杠）、301 关闭、缺失尾斜杠即 404

### Modified Capabilities

- `api-path-normalization`：**移除**「尾斜杠双向容错」需求 —— 该能力随中间件一并删除

## Impact

- 后端：10 个 `apps/*/urls.py`、`config/settings.py`、删除 `gateway/normalize_slash.py` 与 `MIDDLEWARE` 项
- 前端：模块 api 层的路径串（相对 `baseURL=/api`，需补尾斜杠）
- 测试：`tests/api/case/*.yaml`（45 处）、新增严格语义用例、删除中间件用例
- 工具与数据：`tools/seed_api_endpoints.py`（183 处端点资产路径）
- 文档：`dev_docs` 中约 502 处路径引用、OpenAPI schema
- **破坏性**：严格模式下，任何仍发送无尾斜杠路径的调用方将收到 **404**
