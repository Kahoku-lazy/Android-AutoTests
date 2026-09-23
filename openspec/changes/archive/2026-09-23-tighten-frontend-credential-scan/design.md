## Context

动机见 proposal.md。现状（2026-09-23 本地实测）：

- CI 规则 5 原文：`grep -rnE "(api_key|password|token|secret)\s*[=:]\s*['\"]\w{8,}" frontend/src/ --include="*.js" --include="*.vue" | grep -v node_modules | grep -v ".test."`
- 实际命中 2 处，均为 Vue 属性绑定：`LoginView.vue:135 v-model:password="loginPassword"`、`LoginView.vue:148 v-model:password="regPassword"`。
- 本地实现 `tools/check_gates.py` 的 `cred-frontend` 逐条照搬了该规则，因此本地与 CI 误报一致。
- 约束一：CI 侧用 `grep -rnE`（POSIX ERE），**不支持 lookbehind / lookahead**，无法用一次匹配完成"前面不是 `:`"的判定。
- 约束二：本地与 CI 必须保持同一判定口径，否则 `python run.py check` 的结论不再可信。

## Goals / Non-Goals

**Goals:**

- 消除 Vue 属性绑定造成的误报，使该门禁的命中即代表真实可疑点。
- 本地与 CI 同步收紧，口径仍为一份。

**Non-Goals:**

- 不提升规则的整体检出能力（如覆盖含 `-` 的密钥值、模板字符串）——那是另一件事。
- 不引入新的扫描工具或依赖。
- 不改动其余 4 条凭据规则。

## Decisions

### 决策 1：用「追加一条排除管道」实现，不用 lookbehind

CI 侧为 `... | grep -vE "[:.\-](api_key|password|token|secret)\s*[=:]"`。

- 理由：POSIX ERE 无 lookbehind，无法在一次匹配里表达"前一个字符不是 `:`"；`grep -vE` 是等价且 ERE 兼容的做法。
- 语义等价性：`grep -vE` 是**行级**排除（整行匹配即剔除），本地实现必须同为行级正则排除，不能用"仅看命中位置前一个字符"的实现，否则两端会分叉。
- 备选：改用 `grep -P` 写 lookbehind。被否——依赖 PCRE 支持，且 CI 其他规则均用 ERE，混用增加维护面。

### 决策 2：排除前缀取 `[:.\-]` 三个字符

- `:` 覆盖 Vue 属性绑定（`v-model:password`、`:token`）与对象字面量的分隔符邻接情形；
- `.` 覆盖属性访问（`obj.password`）；
- `-` 覆盖连字符命名（如 `x-password`）。
- 取舍：这会同时排除 `form.token = "abcd1234"` 这类**对象属性赋值**——它可能是真实的硬编码凭据。选择接受该漏报，原因是当前规则的信噪比为 0（2 命中全为误报），先修复"不可用"，再谈"更全"。
- 备选：只排除 `:`。被否——`:token` 之外，`v-model:password.trim="..."` 等变体仍会命中，且 `.`/`-` 前缀同属明显非赋值语境的写法。

### 决策 3：本地 `grep_gate` 增加 `exclude_patterns`（正则排除），与既有 `excludes`（子串排除）并存

- 理由：既有 `excludes` 是子串包含判断（对应 CI 的 `grep -v "PASSWORD"` 这类写法），无法表达 `\s*[=:]` 这样的结构；本次需要正则排除，故新增参数，语义对应 CI 的 `grep -vE`。
- 备选：把 `excludes` 全部改成正则。被否——会改动其余 4 条规则的行为，超出本变更范围。

### 决策 4：不与"含 `-` 的密钥值"缺口一并在本变更中处理

- 事实：`api_key = "sk-live-abcdefgh"` 在**原规则**下就不匹配（`\w{8,}` 不成立），不是本次收紧造成的。
- 处理：记录为已知缺口（tasks 第 5 组），不在本变更扩大规则能力，避免混入两类改动导致结论不可归因。

## 模块防火墙自检

本变更只改 CI workflow 与开发期检查脚本，不涉及业务代码：

- 跨 App import：不涉及。
- 跨 App import service / runner / consumer / state_machine：不涉及。
- INSERT / UPDATE / DELETE 收敛到 api.py：不涉及（无写库行为）。
- 前端不直连数据库、仪表盘不做写操作：不涉及。

无新增跨模块依赖。

## Risks / Trade-offs

- [排除 `[:.\-]` 前缀会漏掉对象属性赋值形式的真实硬编码] → 已作为已知边界写入 proposal 的 Impact；后续若需覆盖，应另立变更并重新设计规则（例如改为"值必须为高熵字符串"）。
- [两端实现分叉，本地与 CI 结论不再一致] → tasks 要求同时改动两处，并用同一组样本（真阳性 / 误报）分别核对两端口径。
- [收紧后该门禁再无命中，掩盖真实问题] → 本变更只消除误报；`python run.py check` 实跑需复现"收紧前 2 → 收紧后 0"，并保留真阳性样本的抓取验证。

## Migration Plan

- 生效方式：合并后本地与 CI 均按新规则执行，无部署步骤。
- 验证：脚本核对（收紧前 2 处命中 → 收紧后 0 处；真阳性样本仍被抓到；误报样本被排除）；再跑 `python run.py check` 确认 `cred-frontend` 转通过。
- 回滚：删除 CI 的排除管道与本地 `exclude_patterns` 参数值即可，单点改动。

## Open Questions

- 是否补上"含 `-` 的密钥值"这一既有缺口：属独立变更，不影响本变更的任务拆分。
