## Why

四道检查（ruff `engines/` ×2、eslint、vue-tsc、prettier `.ts`）自接入起一直处于**仅警告**状态，加上本次新增的静默吞异常检查，共 5 类 6 项告警级门禁。告警级门禁不阻断构建，长期看等于没有门禁——这正是本仓库此前"规则存在但无人执行"的病根。

它们的存量现已全部清零（`.ts` 格式 98 → 0、类型报错 3 → 0、静默吞异常 8 → 0、`engines/` 本就 0），具备转为拦截的条件。

## What Changes

- `tools/check_gates.py`：6 项门禁由告警级改为**拦截级**（`blocking=True`）——`ruff-engines-format` · `ruff-engines-lint` · `eslint` · `vue-tsc` · `prettier-ts` · `silent-except`；描述文案去掉"仅告警"字样。
- `tools/check_gates.py`：新增 `--only <名称,名称>` 过滤参数，供 CI 单独调用某一项（静默吞异常检查不是 CI 内联项，需要该入口；避免在 CI 里重复实现同一段 AST 逻辑）。
- `.github/workflows/ci-phase1.yml`：job `advisory-checks` 更名为 `static-checks`，6 个步骤去掉 `|| { echo "::warning::"; exit 0; }` 包裹改为直接失败；新增 `Silent exception check` 步骤（`python tools/check_gates.py --only silent-except`）。
- `AGENTS.md`：把「已知盲区登记」改为「门禁清单」，登记 6 项均为拦截型并记录存量清零；显式保留「Vue 文件体积仍红」这一项。
- **BREAKING**：对开发流程是**有意收紧**——此后违反上述检查会直接失败；对运行期行为无影响。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更为门禁强度调整，需求来源为用户对"存量清零后转拦截"的决策，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。检查强度与 CI 配置调整，不改变系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 改动文件：`tools/check_gates.py`、`.github/workflows/ci-phase1.yml`、`AGENTS.md`。
- 不涉及 `apps/` 业务代码、API 契约、数据模型、前端页面或依赖。
- 后果：本地 `python run.py check` 与（若 CI 能执行）`static-checks` job 会因这 6 项失败而失败。
- **仍红的一项**：Vue 文件体积（6 个文件超 500 行）属既有拦截型门禁、尚未清算，不在本变更范围；因此当前整仓门禁整体仍非全绿。
- 验证限制：按 `AGENTS.md` 的测试范围收敛条款，本变更**未**运行全量 `python run.py check` 来确认"整体仅剩体积一项红"；各项单独验证结论见 tasks。
