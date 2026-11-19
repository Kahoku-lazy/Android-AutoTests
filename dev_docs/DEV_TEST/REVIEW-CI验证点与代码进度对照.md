# REVIEW — CI 验证点与代码进度对照（2026-11-19）

> 调查方式：读 `.github/workflows/ci-phase1.yml`（HEAD 版与工作树版）、`utils/check_gates.py`、
> `utils/gen_arch_stats.py`、`utils/check_openapi_coverage.py`、`tests/` 测试资产、git 历史与远端状态；
> 并实跑 `python run.py check`（本地全量门禁，约 9 分钟）取证。
> 本文只做分析与建议，未改任何平台代码。

## 0. 结论先行

**总判断：门禁体系一直在跟着代码演进（方向正确），但当前存在「三重脱节 + 一个结构性缺口」。**

1. **远端 CI 落后于本地门禁**：GitHub 上实际运行的仍是旧版 6 job 工作流（`origin/Kahoku` = `0876aeca`）。
   2 job 重构、4 项新门禁/扩围（`single-agent-constructor`、`style-gates`、凭据扫描扩到 engines 与 .ts、
   引擎依赖方向检查）全部躺在**未提交**的工作树里，且这次 CI 重构**没有对应的 OpenSpec 变更记录**。
2. **当前工作树代码自身门禁不绿**：实测 `run.py check` 阻塞项 **18/27 通过、9 项失败**。
   按现状推送，CI 必红。失败集中在：格式/lint（可自动修复）、OpenAPI 基线缺 5 条新端点、
   2 个前端旧测试 spec 的类型夹具没跟上新 DTO。
3. **即使在 HEAD 版本，「本地门禁 = CI」也已不成立**：`dashed-whitelist`、`engines-agents-retirement`
   两道阻塞门禁在本地跑、CI 从未点名；`style-gates` 同样未接 CI。AGENTS.md 的验收口径（工作树已改成
   「python / frontend 两个 job」）领先于已提交的 CI（HEAD 仍写「6 个 job」）。
4. **结构性缺口（最重要）**：CI 对后端 174 个测试文件**只收集、不执行**（`pytest --collect-only`），
   而前端 89 个 spec 全部真跑。计费（`eval_billing`）、授权（grant/author）、发布冻结（release）这类
   行为关键路径的回归在 CI 里**零守护**。测试已 sqlite 内存化（`tests/test_settings.py`），
   unit + integration + arch 共 138 个文件**无需任何外部服务即可在 CI 执行**，补齐条件已经具备。

**最高价值动作（按序）**：① 推送前修掉 9 项红门禁；② CI 重构与门禁脚本、AGENTS 口径**同一提交**落库；
③ CI 增加「后端 unit + integration 测试执行」门禁；④ 增加 `makemigrations --check` 迁移漂移门禁。

---

## 1. 现状盘点

### 1.1 三个版本的 CI 口径

| 版本 | 位置 | 形态 | 状态 |
|---|---|---|---|
| 远端实际运行 | `origin/Kahoku` = `0876aeca` | 旧版 6 job：backend-check / frontend-check / static-checks / security-scan / boundary-check / frontend-quality | GitHub 正在用的就是它 |
| 本地 HEAD | `a4cc01a0`（未推送，仅 docs(readme)） | 同上 6 job | 与远端 CI 一致 |
| 工作树 WIP | 未提交（261 个改动文件的一部分） | 新版 2 job：`python`（18 门禁）/ `frontend`（9 门禁），全部点名 `utils/check_gates.py` | 设计正确，但未落库、无 OpenSpec 记录 |

### 1.2 门禁覆盖对照（以工作树 `build_gates()` 的 27 阻塞 + 3 告警为基准）

| 门禁 | 远端 CI（6 job） | WIP CI（2 job） | 备注 |
|---|---|---|---|
| django-check / ruff-format / ruff-lint | ✅ | ✅ | |
| pytest-collect | ✅ | ✅ | **只收集不执行**（见 §3.1） |
| openapi-schema / openapi-coverage | ✅ | ✅ | 契约门禁有效，本次正确拦下基线漂移 |
| ruff-engines-format / ruff-engines-lint | ✅ | ✅ | |
| silent-except / business-asset | ✅ | ✅ | |
| vitest / vite-build / prettier / eslint / vue-tsc / prettier-ts | ✅ | ✅ | 前端 89 spec 真跑 |
| boundary | ✅（旧口径） | ✅（**新增引擎依赖方向**） | engines 禁 django/apps、底座禁反向依赖 |
| vue-file-size / mock-data | ✅ | ✅ | |
| cred-password / cred-apikey / cred-secret | ✅（仅 backend 范围） | ✅（**扩到 engines**） | |
| cred-frontend | ✅（仅 .js/.vue） | ✅（**扩到 .ts**） | src 下 126 个 .ts、0 个 .js，旧扫描对 TS 全盲 |
| **dashed-whitelist** | ❌ 未点名 | ✅ | HEAD 起就是本地阻塞项，CI 一直漏接 |
| **style-gates** | ❌ 未点名 | ✅ | 同上 |
| **engines-agents-retirement** | ❌ 未点名 | ✅ | 同上 |
| **single-agent-constructor** | ❌（不存在） | ✅ | WIP 新增 |
| cred-default-pwd / inline-style / engines-agents-style | 告警 | 告警（不入 CI） | 有意排除，口径一致 |

> 结论：WIP 版 CI 与本地门禁**首次完全对齐**（27 阻塞门禁全点名）；但远端 CI 缺 3 道既有阻塞门禁 + 2 处扫描扩围 + 1 道新门禁。

### 1.3 代码更新进度（工作树未提交批次，261 文件）

- **2 个活跃 OpenSpec 变更，任务已全部勾完**：`assistant-author`（作者授权）、`assistant-release-eval`
  （草稿/发布冻结/五把纯函数尺子评测）。验证均靠**本地** pytest（含对开发机后端的 api 测试），未经 CI。
- **8 个变更已归档但未提交**（assistant-live-eval、model-use-grant、ops-agent-role-kind、
  workflow-orchestration-kinds、queue-workflow-tasks、task-outcome-closeout、govee-thinking-tool-choice、
  sync-harness-capability-specs）。
- **9 个新迁移**：ai_assistant 0076–0081、bug_manager 0004、task_list 0009/0010（含发布冻结数据迁移）。
- **后端新件**：`eval_billing / eval_rulers / eval_samples / live_rulers / live_runner` 5 个服务 +
  `task_list/workflow_snapshot.py`。
- **engines 新件**：`tools/case_library/`、`tools/document/` 2 个工具包 +
  `workflow/eval_probe / fake_world / goal_case / team_breakdown` 4 个模块。
- **前端新件**：`ai-assistant/evals.vue`（175 行，体积门禁达标）、ops-console 2 组件、3 个新 spec。
- **测试新件**：18 个新后端测试文件（unit 为主，含 django_db sqlite 标记）+ 3 个前端 spec。
- **文档口径**：AGENTS.md 验收从「6 个 job」改为「python / frontend 两个 job」（未提交）。

---

## 2. 实测证据：`python run.py check`（2026-11-19 上午，工作树现状）

**阻塞项 18/27 通过，9 失败；告警项 3/3 通过。退出码 1。**

### 2.1 失败清单（全部可修，多数可自动修）

| 门禁 | 失败点 | 修复方式 |
|---|---|---|
| ruff-format | `backend/apps/ai_assistant/services/eval_rulers.py`、`backend/apps/bug_manager/extract.py`、`backend/apps/task_list/api.py` | `ruff format` 自动 |
| ruff-lint | I001 ×3：`ai_assistant/urls.py`、`ops_console/api.py`、`ops_console/urls.py` | `ruff check --fix` |
| ruff-engines-format | `engines/backend_bridge/agents/tool_selection.py` | 自动 |
| ruff-engines-lint | I001 ×2：`engines/ae_harness/knowledge/store.py`、`tool_selection.py` | `--fix` |
| prettier（vue/js/css） | `AssistantCard.vue`、`SopWorkflowEditor.vue`、`ai-assistant/index.vue` | `prettier --write` |
| prettier-ts | `ai-assistant/helpers/sop-card.ts`、`task-list/constants.ts` | `--write` |
| **vue-tsc** | 4 处类型错，全在**旧 spec 夹具**：`tests/ai-assistant/p0/assistant-card.spec.ts` 缺 `orchestration/kind/leader_name/member_count`；`sop-form.spec.ts` ×3 缺 `orchestration/leaderId/members` | 手工补夹具字段（DTO 已改、spec 未跟） |
| **openapi-schema** | 生成结果与基线不一致 | 重生成基线并随本次接口改动提交 |
| **openapi-coverage** | 5 条新端点未入基线：`/api/ai/assistants/{}/publish/`、`/api/ai/sop-workflows/{}/publish/`、`/api/ops/users/{}/grant-author/`、`/api/ops/users/{}/model-grants/`、`/api/ops/users/{}/revoke-author/` | 同上：`python manage.py spectacular --file openspec/openapi.yaml --validate --fail-on-warn` |

### 2.2 通过项里的亮点（说明门禁在正确守护新代码）

- **vitest 89 个 spec 全绿**、vite-build 绿 —— 前端行为层守护有效。
- **boundary 绿**（含 WIP 新增的引擎依赖方向）：engines 全树 **0 处** django/apps 导入，边界白名单为空（零已知债）。
- **single-agent-constructor / engines-agents-retirement / business-asset / silent-except 绿**：
  新 engines 模块没有绕过 creator.py 构造 Agent，退役面无复活。
- **cred 五项全绿**（含扩围后的 engines 与 .ts）。
- **style-gates / dashed-whitelist / vue-file-size / mock-data 绿**：新前端件符合 Doodle Craft 口径。
- **pytest-collect 绿**：174 个测试文件（含 18 个新件）全部可导入 —— 但也仅止于可导入。

---

## 3. 缺口分析（验证点 vs 代码实现）

### 3.1 后端测试只收集不执行 —— 最大结构性缺口
- 测试资产：174 文件 = **unit 126（含 arch 契约 19）/ integration 12 / api 35 / e2e 1**。
- CI（新旧两版）都只跑 `--collect-only`；`tests/AGENTS.md` 明确 arch 契约测试「必须留在默认单元套件内」
  才有守护作用 —— 现状是 CI 从未执行它们，API 路径对拍、鉴权姿态成对、前后端校验文案一致等契约**在 CI 里不设防**。
- 新功能的钱与权限逻辑（`eval_billing`、grant/author、release 指纹认账）只有本地跑过；
  「CI 是唯一质量闸门」 currently 名不副实（后端行为层）。
- **补齐零障碍**：`tests/test_settings.py` 用 sqlite `:memory:`，conftest 已注册 `utf8mb4_bin` 排序规则；
  unit/integration/arch 不依赖 MySQL、不依赖运行中的服务。`-m "unit or integration"` 即可覆盖 138 文件。
  api（需 `localhost:8766` 运行后端 + 种子账号）与 e2e（需浏览器）留在本地或另设 nightly。

### 3.2 无迁移漂移门禁
- 全仓没有 `makemigrations --check`；`django-check` 不查缺迁移，pytest `--nomigrations` 直接按模型建表 ——
  **模型改了没生成迁移、迁移链断了，CI 与测试都发现不了**。
- 本批恰有 9 个新迁移 + 1 个发布冻结数据迁移（release-eval 任务 4.2），风险敞口真实存在。

### 3.3 OpenAPI 契约门禁有效，但基线落后于代码
- 门禁正确拦下 5 条新端点（§2.1）—— 这是「CI 验证点跟上了、代码侧没跟上」的正面例子。
- 注意历史教训（commit `13d2683f`）：脏树重生成会把并行 WIP 混入基线；基线必须与本批接口改动同提交。

### 3.4 类型门禁有效，spec 夹具落后
- vitest 绿但 vue-tsc 红：运行时没问题、类型契约破了（旧 spec 夹具缺新 DTO 字段）。
  两道门禁互补，缺一不可；也说明「改 DTO 必须同步改 spec」应进变更任务清单。

### 3.5 工具链版本未钉死（本地 ≠ CI 的隐性漂移源）
- ruff：CI `pip install ruff` 装最新，本地 0.17.3，requirements.txt 无 ruff —— 格式判定随版本漂移
  （本次 `extract.py` 的三元表达式重排风格即版本敏感项）。
- Node：CI 20，本地 24；package.json 无 engines 字段。Python 3.13 两侧一致 ✅。Django==6.0.6 钉死 ✅（且有注释说明原因）。

### 3.6 死依赖拖慢 CI
- `evalscope / deepeval / maseval` 在 requirements.txt，但**全仓零引用**（评测实现走的是纯函数尺子）。
  三个重包每次 CI 白装，挤占 20 分钟 timeout。

### 3.7 engines 风格/docstring 门禁只在本地告警
- `engines-agents-style` 为 advisory 且不入 CI；本次实测**已通过**，具备转阻塞条件。
  6 个新 engines 模块的 docstring 义务目前只有 skill 手工查，CI 不兜底。

### 3.8 残留配置
- `pull_request` 触发仍在（仓库已无 PR 流程）；旧 CI 的 `OPENAI_API_KEY` 占位已退役（WIP 已改为三把钥匙，保持即可）。
- `cancel-in-progress: true`：连续推送会取消前一次运行，「推送后确认全绿」应以最新一次运行为准（可接受，需知晓）。

### 3.9 门禁点名的双源漂移风险（本次问题的根因）
- 新设计仍要求「改 `build_gates()` + 改 YAML `--only` 清单」两处同步 —— dashed-whitelist / style-gates /
  retirement 漏接 CI 正是这种漂移。建议给 `Gate` 加 `job` 归属，CI 只跑 `--job python|frontend`，
  新增门禁只改一处，YAML 永不再动。

### 3.10 其他
- ruff 范围不含 `tests/` 与 `utils/`：测试代码无 lint 守护（历史已知 31 处告警在门禁外）。
- 根目录有 `result.json`、`_acl-recovery/` 未跟踪件，违反 temps/ 约定；CI 不管仓库卫生，提交清单应清理。
- 261 文件一批推送违反「一次提交只做一件事」，CI 红时难以归因；应按 OpenSpec 变更拆分提交。

---

## 4. 建议（按优先级）

### P0 —— 本次推送前必须做
1. **修掉 9 项红门禁**（§2.1 清单）：`ruff format` + `ruff check --fix` + `prettier --write` 一把梭；
   手工补 2 个 spec 的类型夹具；重生成 OpenAPI 基线（5 条新端点）。修完重跑 `python run.py check` 至 27/27。
2. **CI 重构落库**：`ci-phase1.yml` + `check_gates.py` + `gen_arch_stats.py` + AGENTS.md 口径**同一提交**
   （`chore(ci): ...`），保证文档描述的 CI 与运行的 CI 永不脱节；按变更逐文件 `git add`（禁 `-A`），
   功能代码按 OpenSpec 变更拆分提交。
3. **补流程**：CI 重构按规则 1 补 OpenSpec 变更记录；AGENTS.md 验收口径（6 job → 2 job）按规则 4
   属于准入/验收条款改动，先提「变更申请」（改什么/为什么/影响面/怎么回退）经确认再落。
4. **CI 增加后端测试执行门禁**：python job 增跑
   `python -m pytest -c tests/pytest.ini -m "unit or integration" -q`（sqlite，无外部服务；arch 契约含在内）。
   这是把「CI 是唯一质量闸门」做实的最小一步。

### P1 —— 短期内跟进
5. **迁移漂移门禁**：`python manage.py makemigrations --check --dry-run`（占位 env 即可）；
   可选加迁移链冒烟（sqlite 上 `manage.py migrate`）。
6. **门禁单真相源**：`Gate.job` + `--job` 过滤，YAML 不再手写 `--only` 清单（根治 §3.9）。
7. **钉工具链**：ruff 进 requirements（或 requirements-dev）并钉版本；Node 对齐（CI 20 → 24，或仓库加
   engines/.nvmrc 统一）；删除或确认 `evalscope/deepeval/maseval` 三个死依赖。
8. **清理残留**：`pull_request` 触发、退役占位 key（WIP 已做，保持）。

### P2 —— 中期可选
9. `engines-agents-style` 转阻塞并接 CI（当前全绿，条件已具备）；docstring 检查同理。
10. api 层 nightly job（CI 内起 sqlite 后端再跑 35 个 api 文件）；e2e 维持本地。
11. ruff 范围扩到 `tests/`、`utils/`（先清存量告警）。
12. 可选：pytest-cov 覆盖率基线、`openspec validate --strict` 门禁、仓库卫生检查（根目录临时件）。

---

## 5. 需要决策的内容

1. **是否批准 CI 增加「后端 unit + integration 测试执行」门禁？**（建议批准；范围 138 文件，sqlite 零服务）
2. **CI 重构补 OpenSpec 记录 + AGENTS 验收口径变更申请**，是否同意按规则 4 走申请后落库？
3. **evalscope / deepeval / maseval 三个零引用依赖**：删除，还是保留为后续评测框架预留？
4. **Node 版本**：CI 对齐本地 24，还是本地降回 20（加 engines 字段钉死）？
5. **engines-agents-style 转阻塞时机**：本次随 CI 重构一起，还是单独下一单？
