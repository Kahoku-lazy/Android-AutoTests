## Context

现状（见 proposal.md - Why）：设备提示词只有一条读取路径与一条写入路径，写库全在 `api.update_device_prompts()`（三份一起、空值拒绝、不部分更新）；前端编辑入口在来源顶部工具栏，三个角色下拉头右上角为空。**没有任何历史/备份表**，最新迁移为 `0041`。

本设计需要回答的问题：存档以什么粒度记、存在哪里、淘汰与唯一性怎么保证不漂、以及在哪些出口触发自动保存。

## Goals / Non-Goals

**Goals:**

- 每次提示词写库都有迹可循：自动存档滚动保留最新三份。
- 手工保存能留一份长期存档，且不被自动淘汰动到。
- 手工保存前有明确确认；退出编辑自动落库。
- 能从历史存档安全地覆盖当前提示词（覆盖前先留档）。

**Non-Goals:**

- 不改提示词正文的读写语义（三份一起、空值拒绝、不部分更新）。
- 不为其它"直接改库"动作（删 Skill、工具启停等）做备份。
- 不做版本 diff 视图、不做自动档的手动删除、不做历史播种。
- 不引入新依赖、不引入后台任务。

## Decisions

**D1 存档粒度 = 一次写入动作一组（planner + executor + verifier 同存为一条记录）。**
理由：写库本来就是一次提交三份；"覆盖之前的备份记录"按**动作**记账最自然，抽屉里一行即一版。备选：每个角色各自三份——条目数 ×3、抽屉难读、恢复时要三次配对，舍弃。

**D2 新模型 `AIDevicePromptArchive`（表 `ai_device_prompt_archive`）。**
字段：`agent`(FK→AIAgent, on_delete=CASCADE) · `kind`(`auto`｜`permanent`) · `planner`/`executor`/`verifier` TextField · `created_by` CharField(超管 user_id) · `created_at`/`updated_at`；`Meta.ordering = ["-created_at", "-id"]`。
理由：与 `AIAgent` 的三列同构，便于预览与恢复；`kind` 单列即可表达两类档。备选：整组存一份 JSON 字段（不选，长 Markdown 独立列更便于定位与断言）；复用 `AIAgent` 加版本列（不选，历史是多行）。

**D3 永久档的唯一性由 `api.py` 的覆盖式 upsert 保证，不加 DB 条件唯一约束。**
理由：项目主库是 MySQL，不支持条件唯一索引（partial index），加 SQLite-only 约束会造成跨库行为不一致；写路径唯一入口就是 `api.py`。备选：单独一张"永久档"表（一张表两 kind 更省且可扩展）；条件唯一约束（跨库不一致），都舍弃。唯一性由单测守护。

**D4 自动淘汰在写库的同一 `transaction.atomic()` 内完成，并按 id 倒序保留最新三条。**
理由：避免"计数—删除"之间的竞态；同一秒内可能写入多条，按时间戳排序不稳，按自增 id 更可靠。删除集合 = 该智能体 `kind='auto'` 记录里除最新三条之外的全部。

**D5 接口形态：写库动作复用 `POST /api/ai/device-prompts/update`，新增 `archive` 参数（`auto` 缺省 / `permanent`）；历史读取与覆盖另设端点。**
- `GET /api/ai/device-prompt-archives/` 列历史（id / kind / created_at / updated_at / 三份长度，**不回正文**）
- `GET /api/ai/device-prompt-archives/<id>/` 读单份全文（供预览）
- `POST /api/ai/device-prompt-archives/<id>/restore/` 用该存档覆盖当前提示词
- `POST /api/ai/device-prompt-archives/<id>/delete/` 删除永久档
理由：写库与记账放同一请求同一事务，避免前端两次调用之间的中间态；"先留档再覆盖"的顺序与原子性只有服务端能保证（前端做不到）。列表不回正文可避免一次拉四份长文本。

**D6 退出编辑的自动保存由前端在三个明确出口触发，且只在内容变化时写。**
出口：`editing` 由 true→false（取消编辑）、`activeSource` 离开 `prompt`、组件卸载。判定：比较 draft 与已保存的三份正文，全等则跳过（不写库、不留档）。
理由：需求要求"退出编辑自动保存"；把判定放服务端无法区分"读"与"写"。不选"失焦即存"（会把随手点开也算改动）。

**D7 存档相关端点一律仅超级管理员（复用现有 `_is_superuser` 校验）。**
理由：历史正文等同于可复原的旧配置，与编辑同权；提示词正文的读取保持对登录用户开放（现有需求不变）。

**D8 确认文案与保留份数等常量集中在 `frontend/src/modules/ai-assistant/constants.ts` 与后端 `api.py` 顶部。**
理由：避免魔法字符串/数字散落；文案固定为「此次保存会覆盖之前的备份记录，请确认是否覆盖保存」。

**D9 不做历史播种。**
新表初始为空；首次保存即同时产生一条自动档与（覆盖式）永久档。

## 模块防火墙自检

- 只改 `apps/ai_assistant` 内部：`models.py` + 新迁移 + `api.py`（唯一写库入口）+ `views_prompts_drf.py` + `urls.py`；无跨 App import、无跨 App 写库。
- 新模型的读写全部经 `api.py`；View 只分发。
- 前端只改本模块的 `api/toolbox.ts`、`composables/useDevicePrompts.ts`、`components/`；HTTP 仍只经 `shared/api-client`；不新增共享件、不直连数据库。
- 本设计不引入新的跨模块依赖。

## Risks / Trade-offs

- [自动淘汰与永久档互相干扰] → 淘汰只作用于 `kind='auto'`，且与写入同事务；单测断言"四次保存后 auto=3、permanent=1 且内容不变"。
- [退出编辑误把"只是看看"变成写库] → 只在三份正文真正变化时写；无改动不写不留档，有单测。
- [覆盖流程中途失败留下半截状态] → restore 全程一个事务：先写自动档、再覆盖提示词，任何异常整体回滚（当前提示词与存档都不动）。
- [历史正文泄漏给非超管] → 四个历史端点全部强制超管，403 用例守护。
- [MySQL 无部分唯一索引] → 唯一性由 `api.py` 单点 upsert 保证 + 单测守护；不依赖 DB 约束。
- [抽屉一次拉四份长文本] → 列表接口只回摘要，正文走详情接口按需拉取。
- [迁移只新建表] → 无数据回填、无破坏性操作；回滚删表即可，不影响现有提示词。

## Migration Plan

1. `python manage.py makemigrations ai_assistant` 生成 `0042`（仅新建表）。
2. `python manage.py migrate ai_assistant`；本机/CI 均无数据回填。
3. 前后端同批发布（新增端点与 `archive` 参数，前端旧版本仍可工作：缺省 `auto`）。
4. 回滚：删除 `0042` 表即可；提示词正文与该功能上线前状态一致。

## Open Questions

（无）
