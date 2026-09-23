## Why

仓库的全部自动检查只存在于 GitHub Actions 的 workflow 里（6 个 job、十余项检查，部分是内联 bash/grep、部分是内联 Python）。一旦 Actions 执行链路不可用（当前账号处于"付款失败"状态，作业不会被分配到运行器，`steps=0`），这些检查就**完全没有其他执行入口**——本地无法一次跑完，只能靠人逐条手敲命令，等于门禁消失。

## What Changes

- 新增 `tools/check_gates.py`：把 CI 的检查项收敛为一份**可本地执行**的检查清单，成为检查内容的唯一真相源。
- `run.py` 新增 `check` 子命令，与既有 `start / stop / restart / status / logs` 并列，委托上述脚本执行。
- 检查分级与 CI 保持一致：
  - **阻塞项**（对应 CI 既有拦截型步骤）：Django 系统检查 · ruff 格式 · ruff lint · 前端单元测试 · 前端构建 · prettier（vue/js/css）· 模块边界检查 · Vue 文件体积检查 · 硬编码凭据扫描 · 硬编码假数据检查 · 内联样式体积检查
  - **告警项**（对应本次新接入 CI 的四类，见变更 `add-ci-warning-gates`）：ruff（`engines/`）· eslint · vue-tsc · prettier（`.ts`）
- 退出码约定：存在阻塞项失败 → 退出码 1；告警项失败只报告，不改变退出码。
- **BREAKING**：无。不改变运行期行为，不新增依赖，不改动 CI workflow。
- 本变更**不**改动 `.github/workflows/ci-phase1.yml`（让 CI 改为调用同一脚本属后续独立变更）。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更为开发工具链改动，需求来源为 GitHub Actions 不可用导致的检查入口缺失，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。纯本地工具链，不引入系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 新增 `tools/check_gates.py`；修改 `run.py`（新增一个子命令）；更新 `AGENTS.md` 「项目工具」一节登记该命令。
- 不涉及 `apps/` 各模块、前端页面、API 契约、数据模型或依赖。
- 检查内容与 CI 一一对应，但执行环境不同：本地跑的是**同一批命令**，因此结论可比。
- 已知的既有红灯（本地实测，非本变更引入）：prettier（vue/js/css）109 个文件不合规；Vue 文件体积 `CaseBreakdown.vue` 528 行超限。因此 `python run.py check` 首次运行会以退出码 1 结束，属预期。
