## 1. 口径判定

- [x] 1.1 复核规格：`openspec/specs/task-card-sop-form/spec.md` 只允许五个字段（任务标题、智能体、配置 YAML、设备、测试指定用例），`openspec/specs/sop-task-run/spec.md` 要求 csv / json 被拒绝 → 弹窗里的 CSV / JSON 芯片属**旧口径残留**（来源 `changes/archive/2026-10-19-platform-sop-task-run` 的「列出 csv、yaml、json」，已被上述两条规格取代）
- [x] 1.2 复核代码事实：前端 `CONFIG_ACCEPT = ".yaml,.yml"`、`onConfigPicked` 已有扩展名拦截；后端 `attachments.collect_task_files` 已有 `CONFIG_EXTENSIONS = {".yaml",".yml"}` —— 功能上早已只放行 YAML，缺的只是界面不再宣称还有另外两种格式

## 2. 改动

- [x] 2.1 `frontend/src/modules/task-list/components/TaskBoard.vue`：删除「配置」行的 `task-format-row`（`CSV · 暂不可用` / `YAML` / `JSON · 暂不可用` 三枚芯片），改为与「需求文档」字段同构的一行说明「配置只收 YAML：.yaml / .yml，单份，上限 20MB」；验证：该文件内 `CSV` / `JSON` / `task-format` / `暂不可用` 命中 0 处
- [x] 2.2 `TaskBoard.vue:121` 选文件拦截文案 → `配置只收 YAML（.yaml / .yml）`（原文案点名 CSV / JSON）
- [x] 2.3 `frontend/src/modules/task-list/components/TaskBoard.style.css`：删除失去消费方的 `.task-format-row` / `.task-format` / `.task-format.is-on` / `.task-format.is-off` 四条样式（-19 行）；验证：全仓 `task-format` 命中 0 处，文件内 `var(--ai-sticky-bg)` 随之消失（该引用本就是 G6 跨边界借用）
- [x] 2.4 `backend/apps/task_list/attachments.py`：删除只为 csv / json 定制的 `REJECTED_CONFIG_EXTENSIONS` 常量与分支，非 YAML 统一返回 `配置只支持 YAML（.yaml / .yml）`；验证：文件内 `csv` / `json` 命中 0 处，`CONFIG_EXTENSIONS` 校验仍在
- [x] 2.5 `dev_docs/DEV_TEST/前端功能统计-20261025.md` TL-02 第二条同步为「配置只收 YAML（`.yaml/.yml`，单份，≤20MB），界面不提供 CSV / JSON 等其它数据格式」，不再描述「暂不可用」芯片

## 3. 门禁验证

- [x] 3.1 `cd frontend && npx prettier --check 'src/modules/task-list/**/*.{vue,css,ts}'` → `All matched files use Prettier code style!`
- [x] 3.2 `cd frontend && npx eslint src/modules/task-list/components/TaskBoard.vue` → 无输出（0 告警 0 错误）
- [x] 3.3 `cd frontend && npx vue-tsc --noEmit` → 退出码 0
- [x] 3.4 `python -m pytest -c tests/pytest.ini tests/graybox/unit/test_task_attachments.py tests/api/test_task_submit_sop.py -q` → **9 passed**（附件扩展名拒绝路径仍绿）
- [x] 3.5 `cd frontend && npm run lint:styles` → 退出码 1，但**全部为既有 G6 基线**（本仓 `task-list` 长期借用 `--ai-*` 令牌）；本文件命中 12 处与改动前同一集合，行号仅随删除位移，且删掉的芯片样式里的 `var(--ai-sticky-bg)` 本身是命中之一 → 命中数只减不增，未新增违规
- [x] 3.6 `python run.py check`（本地门禁，与 CI 同一批检查）→ **阻塞项 22/22 通过，0 失败**，告警项 2/2 通过，退出码 0（含 django-check / ruff / openapi / vitest / vite-build / prettier / eslint / vue-tsc / 边界 / 体积）
- [x] 3.7 `cd frontend && npx vitest run tests/task-list` → **15 文件 / 114 用例全绿**
