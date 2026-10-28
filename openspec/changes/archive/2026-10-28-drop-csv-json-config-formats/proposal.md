## Why

「新建任务」弹窗的「配置」行仍在渲染三枚数据格式芯片：`CSV · 暂不可用` / `YAML` / `JSON · 暂不可用`。这是 `2026-10-19-platform-sop-task-run` 时期「配置类列出 csv、yaml、json，后两者标暂不可用」的口径残留；该口径已被 `openspec/specs/task-card-sop-form/spec.md` 取代——弹窗只允许五个字段（任务标题、智能体、配置 YAML、设备、测试指定用例），`openspec/specs/sop-task-run/spec.md` 也明确 csv / json 必须被拒绝。

后果是界面在自相矛盾：一边声明产品要按「数据格式」三选一，一边两个选项永远不可点；用户还会误以为 CSV / JSON 排期后会支持。事实是配置只有一种形态（YAML），前端 `accept` 已是 `.yaml,.yml`，后端 `attachments.collect_task_files` 也早已只放行 YAML。

## What Changes

- `frontend/src/modules/task-list/components/TaskBoard.vue`：删除「配置」字段里的三枚格式芯片整行（含 `task-format-row`），改为一行与「需求文档」字段同构的说明文案「仅支持 YAML（.yaml / .yml），单份，上限 20MB」。
- `TaskBoard.vue` 的选文件拦截文案：`配置仅支持 YAML；CSV 与 JSON 暂不可用` → `配置仅支持 YAML（.yaml / .yml）`。
- `frontend/src/modules/task-list/components/TaskBoard.style.css`：删除随之失去消费方的 `.task-format` / `.task-format-row` / `.is-on` / `.is-off` 四条样式。
- `backend/apps/task_list/attachments.py`：去掉只为 csv / json 定制的 `REJECTED_CONFIG_EXTENSIONS` 分支与「csv 与 json 暂不可用」文案，非 YAML 统一返回「配置只支持 YAML」，口径收敛成一条。
- 文档同步：`dev_docs/DEV_TEST/前端功能统计-20261025.md` 的 TL-02 行不再写「CSV / JSON 标暂不可用」。
- **无 BREAKING**：可提交的形态仍只有 YAML，提交契约、字段集与后端校验结果不变（csv / json 仍被拒绝，只是文案不再点名它们）。

## 关联文档

- `openspec/specs/task-card-sop-form/spec.md`：弹窗五字段、「配置 YAML」必须为 YAML。
- `openspec/specs/sop-task-run/spec.md`：`csv 与 json MUST 被拒绝`。
- 取代来源：`openspec/changes/archive/2026-10-19-platform-sop-task-run/`（其「列出 csv、yaml、json」要求已被上两条规格取代）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无）

> 本变更把实现恢复到 `task-card-sop-form` / `sop-task-run` 已定义的形态（配置只有 YAML，不提供其它数据格式），不引入需求级行为变化，`.openspec.yaml` 置 `skip_specs: true`。

## Impact

- 前端：`frontend/src/modules/task-list/components/TaskBoard.vue`、`frontend/src/modules/task-list/components/TaskBoard.style.css`
- 后端：`backend/apps/task_list/attachments.py`（仅文案与分支收敛，校验结果不变）
- 文档：`dev_docs/DEV_TEST/前端功能统计-20261025.md`
- 不影响：提交接口形态（multipart 五字段）、YAML 用例标题解析、设备下拉与轮询
