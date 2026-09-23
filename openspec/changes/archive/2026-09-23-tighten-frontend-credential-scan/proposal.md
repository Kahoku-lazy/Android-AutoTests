## Why

前端硬编码凭据扫描（CI `security-scan` 的规则 5）把 Vue 的属性绑定当作硬编码凭据：当前命中的 2 处全部是 `v-model:password="..."`，属 100% 误报。安全门禁一旦长期误报，使用者会开始无视它，门禁等于失效。

该规则在本地门禁实跑（`python run.py check`）中首次被执行并暴露此问题——此前 CI 从未真正运行过任何步骤。

## What Changes

- `.github/workflows/ci-phase1.yml`：`security-scan` 规则 5 在既有 grep 管道后追加一条排除：`grep -vE "[:.\-](api_key|password|token|secret)\s*[=:]"`，使 Vue 属性绑定与属性访问形式不再被判为硬编码凭据。
- `tools/check_gates.py`：`cred-frontend` 门禁同步该排除项，保持"本地 = CI"的同一判定口径；为此为 `grep_gate` 增加 `exclude_patterns` 支持（正则级排除，与 CI 的 `grep -vE` 语义一致）。
- **BREAKING**：无。仅收紧一条扫描规则的误报，不改变任何运行期行为。
- 不补偿既有缺口：形如 `api_key = "sk-live-..."` 的值因含 `-`、`\w{8,}` 不成立而**在原规则中本就不被匹配**，属既有缺口，记录为已知项（见 tasks）。

## 关联文档

无对应需求编号（未关联 PRD / ARCH）。本变更为开发工具链与 CI 扫描规则修正，需求来源为本地门禁首次实跑发现的误报，已在 proposal 内完整描述。

## Capabilities

### New Capabilities

无。纯工具链修正，不引入系统行为，按 schema 约定置 `skip_specs: true`。

### Modified Capabilities

无。

## Impact

- 仅影响两个文件：`.github/workflows/ci-phase1.yml`、`tools/check_gates.py`。
- 不涉及 `apps/` 各模块、前端页面、API 契约、数据模型或依赖。
- 预期结果：本地门禁阻塞项由 **10/13 通过** 变为 **11/13 通过**（`cred-frontend` 转通过）；整体退出码仍为 1（另有 prettier 109 文件与 Vue 体积 6 文件两项存量红灯未清）。
- 判定边界变化：排除前缀 `: . -` 后，`form.token = "abcd1234"` 这类**对象属性赋值**将不再命中。取舍理由见 design.md 决策 2。
