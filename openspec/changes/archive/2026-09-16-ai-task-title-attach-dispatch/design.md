## Context

动机见 `proposal.md` Why。现码：`POST /api/ai/tasks/submit` 立即 `start_task` + 后台线程；`title=goal[:100]`；`attachment` 为 `CharField(500)` 且不进引擎；`TaskRequest.goal` 仅任务目标；规划工具集为空。Word/PDF→文本解析已存在于 `kb_files.py` 与 `views_upload_drf.py`，与任务提交未接线。需求与验收见本变更 `specs/`。

约束：写库只经 `apps/ai_assistant/api.py`；前端只走模块 `api.ts`；引擎不 import `apps.*`；`TaskRequest` 字段集不扩展中文键。

## Goals / Non-Goals

**Goals:**

- 提交 multipart：标题 + 目标 + 可选 docx/pdf + 可选 serial；解析 Markdown 落库；提交时固化 serial。
- Django 把四字段 JSON 写入 `TaskRequest.goal` 再调引擎。
- DB 级按 serial 抢槽：同设备至多一条 running，结束或重启后再 claim 最早 pending。
- 列表卡片展示标题 / 状态 / 创建时间 / 设备名。

**Non-Goals:**

- 批量建任务 UI；`.doc`（仅 `.docx`/`.pdf`）；附件进入知识库/RAG；自动 `acquire_device`；扩展 TaskStatus；改执行/验收 prompt 与工具集。

## Decisions

1. **规划 JSON 仍走 `TaskRequest.goal`**  
   理由：引擎协议已是「用户输入字符串」；扩四个中文字段会改 `engines/ai/base.py` 与所有引擎实现。备选：新增 `user_input`/`planner_payload` 字段 —— 否决，本单只改 Django 组装与 `PLANNER_PROMPT` 说明。

2. **`attachment` 改为 `TextField` 存 Markdown；另增 `attachment_filename`（可空）**  
   理由：解析后的 MD 远超 500 字；原路径语义废弃。不把原文文件当知识库文档。备选：复用 `POST /ai/upload-file`（解析完删文件）再把 content 塞进 JSON body —— 两次请求且与任务无事务绑定，否决。提交一次 multipart 在 `TaskSubmitAPIView` 内解析并 `create_task`。

3. **解析实现复用 `kb_files._parse_docx` / `_parse_pdf`（抽到可调用函数，禁止复制第三份）**  
   体积上限对齐上传接口 20MB。`.doc` 不支持。解析失败整单 400，不落半截任务。

4. **设备名不另建型号表：提交时把可选 `device_label` 写入（前端选项已有 model）；列表优先 label，否则 serial**  
   理由：任务跑完后设备可能离线，serialize 时再查在线列表会丢型号。备选：每次列表查 `device_pool` —— 否决。

5. **调度在 `api.py`：`dispatch_device(serial)` 于事务内 `select_for_update` 该 serial 全部 `pending|running` 行**  
   - 已有 running → 新任务保持 pending。  
   - 无 running → 将 id 最小的 pending `start_task` 并起现有 `_run_task_async` 线程。  
   `finalize_task` 之后再次 `dispatch_device`。进程启动：现有 `recover_orphaned_tasks` 把遗留 running 标 failed，再对有 pending 的 serial 各调一次 dispatch。  
   备选：Redis 队列 / Channels worker —— 否决，当前就是线程模型，只补互斥。  
   备选：工作流内 `acquire_device` —— 本单不绑设备锁生命周期，避免与 runner 占用前缀语义纠缠。

6. **留空设备：创建前调用已有 `_resolve_device_serial`，失败不建任务；成功后 serial 落库，排队不再重解析。**

7. **前端**：`el-upload` 限 1 个文件、accept `.docx,.pdf`；`submitTask` 改 FormData。卡片 `DoodleNote` header 标题，正文状态/时间/设备名。弹窗仍 `el-dialog` 640px，遵循 doodle-craft 弹窗规格。

## 模块防火墙自检

- 跨 App import：`ai_assistant` 继续只读调用 `apps.device_pool.api.get_online_devices`（已有），不 import manager/views。
- 不跨 App import service/runner/consumer/state_machine。
- INSERT/UPDATE/DELETE `ai_tasks` 只经 `apps/ai_assistant/api.py`（含 dispatch 改状态）。
- 前端不直连数据库；不经仪表盘写任务。
- 引擎仍零 `apps.*`；JSON 在 Django `engine_adapter` 组装。
- 新跨模块依赖：无。

## Risks / Trade-offs

- [docx/pdf 扫描件无文本] → 解析得到空或「无可用文本」仍创建；规划模型可能步骤空泛。缓解：解析异常才 400；全空文本仍提交但附件字段为解析结果。
- [多 worker 线程竞态] → 仅靠内存锁不够。缓解：`select_for_update` 锁该 serial 相关任务行。
- [旧任务 attachment 存的是路径字符串] → 迁移扩列不改历史值；旧任务再跑会把路径当 MD。缓解：不提供「重跑旧附件」；仅新提交走解析。
- [规划 JSON 变长] → 大 PDF 的 MD 可能撑爆上下文。缓解：本单不截断（避免静默丢需求）；若后续超限再单独立限。
- [卡片不再展示目标] → 用户要点进详情才看目标。符合需求 1。

## Migration Plan

1. 迁移：`attachment` CharField→TextField；新增 `attachment_filename`、`device_label`（均可空）。
2. 发布后端后再发前端（FormData）；过渡期旧 JSON body 无 title 应 400。
3. 回滚：恢复文本框附件与立即开线程；已写入的 MD 仍可当字符串读。
