## 1. 收紧 CI 规则

- [x] 1.1 `security-scan` 规则 5 管道末尾追加排除 `| grep -vE "[:.\-](api_key|password|token|secret)\s*[=:]"`；其余 4 条规则未动
- [x] 1.2 YAML 解析通过；`git diff -U0` 核对：本轮仅规则 5 的 1 行被替换为 2 行，无其他行改动

## 2. 同步本地门禁

- [x] 2.1 `grep_gate` 新增 `exclude_patterns`（行级正则排除，对应 CI 的 `grep -vE`），既有 `excludes`（子串排除）行为不变
- [x] 2.2 `cred-frontend` 门禁传入同一条排除正则，本地与 CI 口径一致
- [x] 2.3 `ruff check` 与 `ruff format --check` 对 `tools/check_gates.py` 通过

## 3. 验证收紧效果

- [x] 3.1 真实代码核对：`cred-frontend` 门禁命中由 **2 处 → 0 处**（原 2 处均为 `LoginView.vue` 的 `v-model:password`），门禁结论 FAIL → PASS
- [x] 3.2 真阳性样本仍被抓到 3/3：`const token = "abcdef123456"` · `{ secret: 'abcd1234efgh' }` · `let password = "hunter2hunter2"`
- [x] 3.3 误报样本全部被排除 3/3：`v-model:password="loginPassword"` · `:token="authToken"` · `v-model:secret="apiSecretValue"`

## 4. 端到端复跑

- [x] 4.1 `python run.py check` 实跑：阻塞项 **10/13 → 11/13**（`cred-frontend` 转 PASS）；逐行比对两次运行的 20 行结论，**唯一差异就是这一行**，其余门禁结论未变
- [x] 4.2 整体退出码仍为 1（剩余失败项：prettier 109 个文件、Vue 体积 6 个文件），符合预期

## 5. 记录边界与缺口

- [x] 5.1 判定边界已记录：排除前缀 `: . -` 后，`form.token = "abcd1234"` 这类对象属性赋值不再命中（取舍理由见 design.md 决策 2：当前信噪比为 0，先修复可用性）
- [x] 5.2 既有缺口已记录：`api_key = "sk-live-..."` 因值含 `-`、`\w{8,}` 不成立，在**原规则**下本就不被匹配，非本次收紧造成；属独立变更的候选范围

---

## 结果记录（2026-09-23）

| 项目 | 收紧前 | 收紧后 |
| --- | --- | --- |
| `cred-frontend` 结论 | FAIL（2 处误报） | **PASS（0 命中）** |
| 阻塞项 | 10/13 | **11/13** |
| 告警项 | 5/7 | 5/7（未变） |
| 退出码 | 1 | 1（存量红灯：prettier 109 文件、Vue 体积 6 文件） |

本次改动文件：`.github/workflows/ci-phase1.yml`、`tools/check_gates.py`。
