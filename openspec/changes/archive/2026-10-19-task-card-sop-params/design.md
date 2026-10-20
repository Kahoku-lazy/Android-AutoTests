## Context

现状见 proposal.md - Why。关键代码位置：

- 卡片弹窗：[TaskBoard.vue:177](frontend/src/modules/ai-assistant/components/TaskBoard.vue#L177)，状态在 [useTaskPublish.ts:41](frontend/src/modules/ai-assistant/composables/useTaskPublish.ts#L41)。
- 提交入口：[views_drf.py:718](apps/ai_assistant/views_drf.py#L718) + `TaskSubmitInputSerializer`（[serializers.py:209](apps/ai_assistant/serializers.py#L209)）。
- 执行线程：[task_runner.py:21](apps/ai_assistant/task_runner.py#L21)；开场在 [api.py:553](apps/ai_assistant/api.py#L553)。
- 引擎入口：[platform_run.py:58](engines/agents/workflow/platform_run.py#L58)；手工入口 `run_workflow(yml, run_input, case_title)`（[ui_auto_workflow.py:141](engines/agents/workflow/ui_auto_workflow.py#L141)）。

## Goals / Non-Goals

**Goals:**

- 新建任务弹窗只剩五个字段，智能体必选，参数随智能体确定（当前只有 `sop`）。
- 指定用例只跑一条；空=全部；不存在时给可读失败。
- 执行开场固定为设备序列号模板，不再拼目标/文档。
- 后端落 `case_title`，克隆重跑保留。

**Non-Goals:**

- 不做多智能体 fan-out（智能体单选）。
- 不做多份 YAML。
- 不改 SOP 的步骤/重试/验收和工具装配。
- 不删历史任务的 `goal` / 文档数据，也不改历史详情展示。

## Decisions

### D1 前端：智能体单选必选，参数组由「流程」决定

- 下拉选项来自 `listAgents()` 的智能体列表；当前唯一选项显示 `route_configs.device_control.name`（Agent-01号）。
- 选中值存 `agent_id`；未选时 `canSubmit()` 返回 false，提交按钮置灰。
- 当前只有 `sop`，参数组固定为 YAML + 设备 + 用例；后续新增流程时在 `helpers/agent-params.ts` 里按智能体/routing 配置扩展，不在组件里堆分支。
- 备选：保留「未选智能体 → 目标+文档」双模式（用户已否决：未选不允许提交）。

### D2 YAML 标题在前端解析（js-yaml）

- 新增依赖 `js-yaml` + `@types/js-yaml`；纯函数 `parseCaseTitles(text)` 返回 `{ titles, error }`。
- 只读根节点的 `title`；根节点支持单条用例映射或列表（与后端一致）。
- 选文件时用 `file.text()` 读取，解析失败给出可读提示并清空选项；切换文件清空已选用例。
- 备选：后端解析接口（用户选择前端解析，避免多一次请求/新端点）。

### D3 后端契约：`agent_id` 必填，`case_title` 落库

- `AITask` 增加 `case_title = CharField(255, default="", blank=True)`，迁移由 `makemigrations` 生成。
- `TaskSubmitInputSerializer`：`agent_id` 必填；`device_serial` 必填；`case_title` 可选；`goal` 改可选（兼容旧请求）；`assistant_route` 保留可选但不再参与选智能体。
- `TaskSubmitAPIView`：按 `agent_id` 取智能体；调用 `engine_adapter.sop_role_models` 校验执行/验收模型，失败返回 400；设备必填校验；`config` 仍由 `collect_task_files` 校验。
- `api.create_task` / `rerun_task` 增加 `case_title`。
- 备选：新增 `mode` 字段区分旧/新（不必要：新链路只有 SOP 一种执行）。

### D4 执行开场固定模板

- `api.build_sop_run_input(task)` 返回 `本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。`。
- `task_runner` 用它替换 `build_sop_opening`；`build_sop_opening` 无其他调用方后删除。
- 旧任务重跑同样走新模板（goal/docs 不再进入开场），这是本次预期行为。

### D5 引擎按 `case_title` 过滤

- `run_platform_sop(..., case_title: str = "")` 在 `validate_platform_yaml` 之后过滤：
  - 空：按文件顺序全部跑；
  - 非空：只保留 `case.title == case_title`；
  - 无匹配：返回 `{load_message: LOAD_OK, status: "fail", reason: f"用例「{case_title}」不存在", completed: []}`。
- 过滤在平台入口完成，`AgentSOPWorkflow` 不改（手工入口的 `case_title` 逻辑保持原样）。

### D6 测试策略

- 前端：`parseCaseTitles` 纯函数用例；`useTaskPublish` 用例覆盖「未选智能体不可提交」「提交字段只有五项」「换文件清空用例」。
- 后端：接口用例覆盖 agent 缺失、设备缺失、YAML 缺失、`case_title` 落库；引擎用例覆盖指定用例/不存在用例。
- 定向跑，不跑全量回归。

## 模块防火墙自检

- 前端只经 `api/tasks.ts` 调 HTTP；新解析纯函数无 I/O。
- 后端 `View → api.py → ORM`；`AITask` 写操作仍集中在 `api.py`（`create_task` / `rerun_task` / `finalize_task`）。
- 引擎不 import `apps`；`case_title` 只作为入参传递。
- 无新增跨 App Model 访问；无新 WS/SSE。

## Risks / Trade-offs

- [旧任务重跑开场变化] → 属于预期；旧任务详情仍显示原目标/文档，执行只按设备序列号。
- [js-yaml 与后端 PyYAML 结构差异] → 前端只取 `title`，后端仍以 `validate_platform_yaml` 为准；前端解析失败仅阻止选用例，不阻止提交（后端会再校验）。
- [历史客户端仍提交 goal/docs] → 字段保留但忽略；在接口文档里注明。
- [迁移编号与并行变更冲突] → 用 `makemigrations` 生成下一个编号，冲突时重排。
