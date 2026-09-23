## 1. 本地门禁转拦截

- [x] 1.1 `ruff-engines-format` / `ruff-engines-lint` 改为 `blocking=True`，描述去掉"仅告警"
- [x] 1.2 `eslint` / `vue-tsc` / `prettier-ts` 改为 `blocking=True`，描述去掉"仅告警"
- [x] 1.3 `silent-except` 改为 `blocking=True`
- [x] 1.4 `check_gates.py` 新增 `--only <逗号分隔>` 过滤：未知名称报错并返回退出码 2；用于 CI 单独调用 AST 检查

## 2. CI 同步

- [x] 2.1 job `advisory-checks` 更名为 `static-checks`，注释说明已由"仅警告"转为"拦截"
- [x] 2.2 五个步骤去掉 `|| { echo "::warning::…"; exit 0; }` 包裹，改为命令直接决定成败
- [x] 2.3 新增 `Silent exception check` 步骤：`python tools/check_gates.py --only silent-except`
- [x] 2.4 workflow YAML 解析通过；job 列表为 backend-check / frontend-check / static-checks / security-scan / boundary-check / frontend-quality；`static-checks` 步骤序列符合预期；文件内已无 `warning only` 步骤名（仅剩说明性注释）

## 3. 文档同步

- [x] 3.1 `AGENTS.md`「已知盲区登记」改写为「门禁清单」，登记 6 项均为拦截型
- [x] 3.2 记录存量清零数据（`.ts` 98→0 · 类型 3→0 · 静默 8→0 · `engines/` 本就 0）
- [x] 3.3 显式保留「Vue 文件体积仍红（6 个文件）」这一事实，避免误读为门禁全绿

## 4. 验证

- [x] 4.1 `--only ruff-engines-lint,silent-except`：两项均 PASS，退出码 0
- [x] 4.2 `--only nope`：输出未知门禁与可用清单，退出码 2
- [x] 4.3 `ruff check` 与 `ruff format --check` 对 `tools/check_gates.py`：通过
- [x] 4.4 人工核对：本次仅改判定级别与 CI 包裹形式，未改动任何检查的命令、作用域或阈值

> **验证范围说明**：按 `AGENTS.md` 测试范围收敛条款，**未**运行全量 `python run.py check`。因此"整体是否只剩体积一项红"是**基于各项单独结论的推断**，不是实测；需要实测请明确要求（单次全量约 4 分钟）。

## 5. 收尾

- [x] 5.1 记录未覆盖项：Vue 文件体积（6 个文件）仍在红，属独立变更范围

---

## 结果记录（2026-09-23）

| 门禁 | 变更前级别 | 变更后级别 | 单项结论 |
| --- | --- | --- | --- |
| `ruff-engines-format` | 告警 | **拦截** | 通过 |
| `ruff-engines-lint` | 告警 | **拦截** | 通过 |
| `eslint` | 告警 | **拦截** | 通过（69 warning / 0 error） |
| `vue-tsc` | 告警 | **拦截** | 通过 |
| `prettier-ts` | 告警 | **拦截** | 通过 |
| `silent-except` | 告警 | **拦截** | 通过 |
| `vue-file-size` | 拦截（既有） | 拦截（未动） | **仍失败：6 个文件超 500 行** |

本地门禁检查总数 21 项，其中拦截项 19、告警项 2（`cred-default-pwd`、`inline-style`，二者在 CI 中本就只提示）。
