## 1. 后端：把落盘失败转成可读 API 错误

- [x] 1.1 在 `backend/apps/task_list/views.py` 增加私有 helper `_store_attachment(filename: str, content: bytes) -> str`：内部调用 `store_flat_upload`；捕获 `OSError` 时先 `backend_log.exception("任务附件写入失败: %s", filename)`，再 `raise APIException(f"任务配置文件写入失败：{exc.strerror or exc}，请检查运行账号对该目录的写权限") from exc`（`APIException` 从 `rest_framework.exceptions` 导入）。验证：`.venv\Scripts\python.exe manage.py check` 通过、`ruff check backend/apps/task_list/views.py` 无告警。

- [x] 1.2 `_submit_assistant_sop`（本地 YAML 与平台用例两来源共用）把 `stored_path=store_flat_upload(prepared.filename, prepared.content)` 改为 `stored_path=_store_attachment(prepared.filename, prepared.content)`。验证：`.venv\Scripts\python.exe -m pytest -c tests/pytest.ini tests/task/api -q` 既有用例全绿。

- [x] 1.3 `_submit_material_workflow` 把 `stored_path=store_flat_upload(filename, markdown.encode("utf-8"))` 同样改走 helper。验证：同 1.2 的 pytest 命令全绿。

- [x] 1.4 收口检查：全仓直接调用 `store_flat_upload` 的只剩 `attachments.py` 的定义与 `views.py` 的 helper；后续新增落盘点必须复用 helper。验证：`rg -n "store_flat_upload" backend/` 输出仅这两处。

## 2. 测试：锁定存储失败契约

- [x] 2.1 新增 `tests/task/api/test_task_submit_storage_error.py`（偏差：DRF 的 `response.data` 仍是 `{detail: ...}`，信封只存在于渲染后的 JSON，断言改为 `response.render()` + `json.loads(response.content)`）：`monkeypatch.setattr("backend.apps.task_list.attachments.store_flat_upload", _boom)`，`_boom` 抛 `PermissionError(13, "Permission denied")`；断言响应 500、`response.render()` 后 `Content-Type` 为 `application/json`、`response.data["status"] is False`、`message` 同时含「写入失败」与「写权限」，且不含 `Traceback`。验证：`.venv\Scripts\python.exe -m pytest -c tests/pytest.ini tests/task/api/test_task_submit_storage_error.py -q` 通过。

- [x] 2.2 同文件补两条：①写盘失败后 `Task.objects.count()` 与提交前一致（原子回滚，任务与附件都不落库）；②成功提交仍返回 `{status: true, data:{id,status}}`，缺 `workflow_id` 仍是 400 + 原「请选择智能体」文案（不被替换成写入失败文案）。（偏差：`TaskSubmitInputSerializer.validate` 先于视图拦截，缺 `workflow_id` 且无 `agent_id` 时返回的是「请选择智能体」；`views.py` 里的「请从工作流提交任务」当前不可达）验证：同 2.1 的 pytest 命令通过（3 条用例全绿）。

- [x] 2.3 平台用例来源的写盘失败走同一文案：构造 `case_source=platform` + `case_ids`，monkeypatch `backend.apps.case_manager.api.automation_case_identity` / `compile_automation_cases` 返回合法里程碑，再让 `store_flat_upload` 抛 `PermissionError`，断言 `message` 与 2.1 同一口径。验证：同上 pytest 命令通过。

## 3. 前端：锁定「500 + message 直接展示」的口径

- [x] 3.1 新增 `frontend/tests/shared/p0/apiError.spec.ts`（偏差：vitest 按 `tests/<模块>/p0|p1` 扫描，放 `tests/shared` 根目录不会被收集）：`formatApiError({response:{status:500,data:{status:false,message:"任务配置文件写入失败：Permission denied，请检查运行账号对该目录的写权限"}}})` MUST 原样返回该 message，MUST NOT 返回「服务暂时异常，请稍后重试」；再断言无 `message` 的 500 仍回落到通用文案（保持既有行为）。验证：`cd frontend; npx vitest run tests/shared/apiError.spec.ts` 通过。

## 4. 门禁与验收

- [x] 4.1 后端门禁（2026-11-26 实跑：阻塞项 30/30 通过）：`.venv\Scripts\python.exe -m run check`（等价 `python run.py check`），退出码 0。

- [x] 4.2 **等价验证（偏差记录：浏览器端到端未做）** —— 2026-11-26 实测：把 `DATA_DIR` 指到 `Z:\nope` 后**后端进程直接起不来**（`run start backend` 报 backend did not start，健康检查期间 MySQL 连接丢失），浏览器路径拿不到那个 500；改用「真实 settings + 真实文件系统」验证同一落盘入口：`temps/probe_storage_error.py` 输出 `status=500`、`message=任务配置文件写入失败：系统找不到指定的路径，请检查运行账号对该目录的写权限`、无 `Traceback`，且 `logs/backend.log` 有 `任务附件写入失败: probe.yaml` 堆栈；界面文案映射由 `apiError.spec.ts` 单独锁定。**未做**：浏览器点「开始运行」的截图。（浏览器）：把 `.env` 的 `DATA_DIR` 临时指向一个不存在的盘符（如 `Z:\nope`）→ `python -m run restart backend` → 弹窗点「开始运行」→ 界面 MUST 显示「任务配置文件写入失败…请检查…写权限」，而不是「服务暂时异常，请稍后重试」；`logs/backend.log` MUST 有对应堆栈；任务清单 MUST 不出现新任务。验完把 `DATA_DIR` 还原并重启后端，正常提交成功。验证：记录界面文案截图与 backend.log 片段。

- [x] 4.3 架构与风格：`gen_arch_stats.py --check-boundaries` 零违规；`module_docstring` 不在 `run check` 门禁内（2026-11-24 起全仓不写注释），本条以 boundary + ruff 为准。原任务文本：`python utils/gen_arch_stats.py --check-boundaries` 退出码 0；`engines-agents-style-check` / docstring 检查仅报本次新增问题（本变更只动 `backend/apps/task_list/views.py` 与测试）。
