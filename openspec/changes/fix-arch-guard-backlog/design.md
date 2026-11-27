## Context

4 条失败都属「守护还在、被守的东西漏了」，不是守护写错。修复原则：**改被守的实现，不改守护的判据**，唯一例外是 API 文档说明的补充机制（守护只要求非空，怎么补是实现的自由）。

## Goals / Non-Goals

**Goals**

- `tests/arch/unit` 全绿，且不是靠放宽断言换来的。
- 每条修复都保持对外契约不变（路径、信封、状态码语义、返回结构）。

**Non-Goals**

- 不重新引入视图 docstring / 模块注释（2026-11-24 的「全仓不写注释」口径不动）。
- 不改 `api-docs-surface` / `auth-session` 的规格文本（行为要求未变）。
- 不顺手清理其它死代码（另立单）。

## Decisions

### D1 写库走 api：加两个窄函数，不做大重构

`save_task_run_payload(task, payload)` 只做「序列化 + 只更新 result 字段」，`clear_tasks()` 只做「删全部任务行并返回计数」。
备选（否）：复用 `clear_agent_tasks()` —— 它还会清媒体存储，直接替换会改变清空端点的行为，属越界。

### D2 删号与停用分开判定

`values_list("is_active", flat=True).first()` 的三种返回正好区分三态：`None`（行不存在）、`True`、`False`。
- `None` → 401「登录已过期或令牌无效」（令牌主体已不存在，本质是令牌失效）
- `False` → 403 + `code=account_disabled`（账号还在，只是被停用）
- 数据库异常 → 放行（沿用既有 fail-open 记录，不在此单改）

### D3 前端：删死文件 + 把动态动作写成内联三元

`agents.ts` 的三个函数无人引用且指向已删除路由，整份删除比改路径更诚实。
`setOpsUserOperator()` 与同文件 `setOpsUserActive()` 统一为模板内联三元 —— 守护能静态枚举出两个真实路径，不再产生 `/ops/users/1/1/` 这种假路径。

### D4 API 文档说明用 postprocessing hook + 规则表

选择理由：
- 130 个端点逐个写 `@extend_schema(summary=…)` 会铺开在 ~20 个 views 文件里，与「去注释」后的代码风格冲突，且新增端点容易漏；
- 规则表（资源中文名 × 动作中文名）集中在一处，新增端点默认也能得到「资源 + 列表/详情/创建/更新/删除」这类可读说明，覆盖不到时回落 `METHOD path`，守护至少不会红。
- hook 只填空缺，不动已有 `summary`/`description`，与将来逐端点精修不冲突。

代价：规则生成的说明不如人工撰写精确；需要精修的端点后续可在 `OVERRIDES` 或视图 `extend_schema` 里补，属渐进改进。

## Risks / Trade-offs

- [规则生成的 summary 千篇一律] -> 关键动作（日志票据、任务媒体、批量停用等）已列 `OVERRIDES`；其余 CRUD 用「资源+动作」足够表达。
- [删号改回 401 会影响前端登录态判断] -> 前端对 401 的处理就是「跳登录」，比 403「账号停用」更符合删号事实；`auth-session` 规格未把删号定为 403。
- [清空任务仍只删行、不删媒体] -> 与修复前完全一致，媒体清理是既有 `clear_agent_tasks()` 的职责，不在本单改语义。

## 模块防火墙自检

- 跨 App import：无新增；`task_list/views.py` 仍只调本 App `api.py`。
- 写库路径：三处 ORM 写移到 `api.py`，View 变纯分发。
- 异常类：不新增；`middleware.py` 只是新增一个 401 分支。
- 依赖方向：`backend/shared/api_docs.py` 只依赖 drf-spectacular 生成结果，零业务 import。
