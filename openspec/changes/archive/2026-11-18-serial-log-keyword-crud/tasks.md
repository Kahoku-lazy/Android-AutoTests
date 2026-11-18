## 1. 实施前协调与批准

- [x] 1.1 核对 `add-serial-log-custom-ports` 落地状态（views/urls/前端是否已提交），确定共享文件（views.py / urls.py / api.ts / constants.ts / LogKeywordPanel.vue）的分区追加方式。验证：实施记录写明对方状态与本单改动分区。
- [x] 1.2 将 design.md「红线变更申请」提交需求方确认（前端「关键词表只读」条款、后端接口表与职责段）。验证：获得明确同意后才允许任务 5.1 动这两份 AGENTS；未获批则停下上报。

## 2. 后端

- [x] 2.1 `api.py` 增 `create_keyword`（唯一键重复抛 ValueError；缺省 scope 通用、feature_id 续编、sort_order 追加）与 `update_keyword`（部分更新；不存在 / 撞车 / 无字段 / 非法 scope 抛 ValueError）；`delete_keyword` 复用。验证：新增 integration 用例（重复拒绝、撞车两行不动、部分更新只改指定字段、续编与追加）与 unit 校验用例全绿；`ruff check` + `ruff format --check` 相关路径通过。
- [x] 2.2 `keywords.py` 目录组装的 features 条目加 `row_id`（条目主键），其余口径不变。验证：integration 断言 row_id 与主键一致；既有目录测试（行序 / 计数 / 空态 / 只读）不改断言仍全绿。
- [x] 2.3 `views.py` 增 `LogKeywordListAPIView.post`（201）与 `LogKeywordDetailAPIView.patch/delete`（200），超管校验 + ValueError→400 可读；`urls.py` 增 `keywords/` POST 与 `keywords/<int:row_id>/` 两路由。验证：api 测试覆盖 201 / 403 / 400（重复 / 撞车 / 不存在）/ 删除不动端口与日志文件；`python manage.py check` 与 `python manage.py spectacular --validate` 通过。

## 3. 前端

- [x] 3.1 `api.ts` 增 `createLogKeyword` / `updateLogKeyword` / `deleteLogKeyword`，`LogKeywordFeature` 加 `row_id`；新增 `helpers/keyword-form.ts` 校验纯函数（keyword/module/feature 必填与长度、scope 白名单、feature_id 可选正整数）。验证：新增 `frontend/tests/serial-log/p0/keyword-form.spec.ts` 全绿；`vue-tsc --noEmit` 通过。
- [x] 3.2 新增 `composables/useKeywordCrud.ts`（开合 / 校验兜底 / CRUD / ElMessage / 成功 reload / 删除二次确认）与 `components/KeywordFormDialog.vue`（el-dialog + sketch-kit，新建/编辑复用，范围 el-select filterable allow-create）；文案进 `constants.ts`。验证：新增编排/弹窗 spec 全绿；`npm run build:check` 与 `npm run lint:styles` 通过。
- [x] 3.3 页面入口向 `LogKeywordPanel.vue` 传 `can-manage`（useAuthUser().isSuperuser）；面板超管页头加「新建关键词」、COLUMNS 追加操作列（编辑/删除，sketch-kit 描边态）、接线弹窗与成功后 reload；非超管恰四数据列、页头仅刷新。验证：面板 spec 断言超管操作列/非超管四列零写控件/新建编辑删除流程；`npx vitest run tests/serial-log` 全绿。

## 4. 测试与边界

- [x] 4.1 后端 serial_log 全量回归。验证：`python -m pytest -c tests/pytest.ini tests/serial_log -q` 全绿（含端口 CRUD 既有用例零牵连）。
- [x] 4.2 架构边界。验证：`python utils/gen_arch_stats.py --check-boundaries` 零违规。

## 5. 文档与关单

- [x] 5.1 凭 1.2 批准修改两份 AGENTS 条款（仅申请范围内文本替换，不动双轨制等其它条款）。验证：diff 仅含申请条款。
- [x] 5.2 OpenAPI 基线随接口改动更新：`python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn`。验证：基线 diff 的 serial-log 段恰为本单三端点；**若工作区仍有其它会话未提交的接口改动混入基线，停下上报协调归属，不得把对方改动带进本单提交**。
- [x] 5.3 本地门禁 `python run.py check` 通过（openapi 项随 5.2 对齐）；逐文件 `git add`（禁 `-A`）、Conventional Commits（如 `feat(serial_log): 关键词页面维护（超管新建/编辑/删除）`）、推 Kahoku。验证：ci-phase1.yml 6 个 job 全绿。

## 6. 验收

- [x] 6.1 浏览器验收：超管账号走新建（含 SKU 专用）→ 编辑 → 删除全流程，核对目录刷新与计数；普通账号核对四数据列、零写控件、403；临时数据经 api 清理。验证：验收记录与截图存 `temps/`，随关单说明提交。

## 实施记录

- **1.2 批准（2026-11-18）**：需求方在会话中明确批准 design.md 红线变更申请；5.1 已按批准范围执行（仅前端红线条款 + 后端接口表/职责段）。
- **测试**：后端 serial_log 93 项、前端 serial-log 84 项全绿；vue-tsc / eslint / lint:styles / vite build / 架构边界零违规。
- **5.2 基线插曲**：首次重生成的基线混入并行会话未提交 WIP 口径，致 CI run 44258854675 的 openapi-schema 失败；用 HEAD 干净 worktree 重生成并核验差异仅属对方已提交区域（serial-log 段零变化），修正提交 13d2683f。
- **5.3 CI**：本单提交 27f498a9 + 修正 13d2683f；自有 run 44259635775 被并行推送的 concurrency 取消（非失败）；含本单的最新 run 44259992823（head 06aa1bf8）六 job 全绿。本地门禁剩余失败项（ruff-format / prettier-ts）经核验属并行会话未提交 WIP（task_list / ops-console），本单文件全干净。
- **6.1 验收（2026-11-18）**：temps/acceptance_keyword_crud.py 真实浏览器 13 项断言全 PASS：超管新建（通用 + allow-create 新 SKU H9999）/ 编辑回填与生效 / 删除二次确认；普通用户无新建按钮、恰四数据列、无行内操作；探针词与临时超管 kw_crud_probe 经 api/ORM 清理，DB 回落 70 行。记录 temps/acceptance_crud_record.md，截图 temps/acceptance_crud_{superuser,dialog,normal}.png。
