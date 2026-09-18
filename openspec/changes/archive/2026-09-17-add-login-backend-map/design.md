## Context

- 前端地图靠 Playwright 真实渲染 + `getBoundingClientRect()` 逐元素测量；后端**没有画面可测**，因此必须换掉「测量源」，否则整份产物会退化成手抄代码
- 可用作后端「真相源」的运行时内省点：`django.urls.get_resolver()`、DRF OpenAPI schema（`/api/schema/`）、`django.apps.apps.get_models()`、`settings.MIDDLEWARE`、各 App `api.py` 的 `__all__`
- 采集必须能**制造并清理**用户数据（注册 / 登录），故必须跑在测试库上：pytest `config.test_settings` + `django_db`，事务回滚
- 前端 `login-layer-map.cjs` 的 `REGIONS` 已有 30 个全局唯一编号与 `file:line`，是现成的左表键

## Goals / Non-Goals

**Goals**：让「登录页上这个东西靠什么后端功能」与「平台还背着用户做了哪些信任动作」两个问题，在同一份自包含 HTML 里可点开、可回溯到 `file:line`，且**过期可被一条秒级命令发现**。

**Non-Goals**：不做全后端（275 条路由）；不改生产代码；不追求自动同步；不解决手写行号漂移。

## Decisions

**D1：用「运行时内省 + 真实请求实测」替代「渲染 + 像素测量」。**

| 方案 | 结论 | 理由 |
|---|---|---|
| 静态读源码 + 手写结论（**否决**） | ❌ | 会产出「看起来对」的图；而实测已经推翻了三个凭读代码会漏的事实（F1/F2/F3） |
| 内省 + pytest 真实请求（**采用**） | ✅ | 状态码/响应体/调用次数/SQL 次数都是**测出来的**，与前端「测像素」同构；且在测试库上可安全制造数据 |

**D2：左表直接复用前端的 `REGIONS` 编号，不另起一套。**

两张图共用同一组 1–30 编号，可并排对照；`REGIONS` 本身入指纹，前端增删元素会让后端图过期。这使「页面↔功能」的关联有一个**唯一且已被前端产物验证过**的锚点。

**D3：`--check` 不跑采集。**

采集需要 pytest + 测试库（秒级到十秒级），而「源码变了没」只需算哈希。故 `--check` 实现为**在任何 Python 子进程之前**返回的独立分支——这是它能当门禁的前提。

**D4：反向孤儿集合必须由实测端点集合校验，手写的「无左键」表不得成为唯一真相。**

右栏的「页面看不见的后端功能」是人工归纳的，容易漏。自检器断言**它必须等于 resolver 里实际的 `/api/auth/*` 端点集合**，把归纳钉在运行时事实上。

**D5：指纹覆盖「后端受管源 + 前端 REGIONS + 生成器自身」。**

后端源决定实测结果；前端 `REGIONS` 决定左表；生成器与模板决定呈现与标注清单。三者任一变化都必须让 HTML 过期。

## Risks / Trade-offs

- [采集依赖测试库与 pytest] → 用 `config.test_settings` + `django_db` 事务回滚；实测确认不写真实库
- [Node 调 Python 子进程在受限沙箱下可能 EPERM] → 采集结果先落 `backend-facts.json`，`.cjs` 优先读缓存文件；子进程失败时报出明确错误而非静默降级
- [左表编号随前端地图变化] → `REGIONS` 入指纹；自检器断言两侧编号集合一致
- [实测结论会随后端行为变化] → 这正是该产物存在的意义：行为变了 HTML 会被判过期并点名文件

## Migration Plan

无。首次运行生成器即产出 HTML 与指纹。回滚 = 删除 `temps/login-backend-map/` 与 `openspec/changes/add-login-backend-map/`。

## Open Questions

1. 是否把本产物与 `login-layer-map` 合并成一份「登录模块前后端联合图」（共用左表，两张右栏）？
2. 若将来扩到全后端（275 条路由），左表应换成什么？端点清单本身？
3. 实测组里依赖 Redis（黑名单）——Redis 不可用时采集应失败还是标注降级？
