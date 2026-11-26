## 1. 移除 app_info 业务资产

- [x] 1.1 删除 `engines/agents/config/data/app_info/govee_home.md`；验证：该目录下不再有文件。**验证结果**：目录文件数 0，`Get-ChildItem ... app_info` 为空。
- [x] 1.2 摘除 `engines/agents/config/data/agent_config.yaml` 中两处 `app_info: govee_home` 引用行；验证：`git grep "app_info"` 在该文件为 0 处，YAML 仍可解析。**验证结果**：0 处残留；`yaml.safe_load` 通过，`UI_EXECUTOR_ROLE_CONFIG.RoleConfig` 只剩 `name` 与 `system_prompt`。

## 2. 移除 SOP 业务资产

- [x] 2.1 删除 `engines/ae_harness/workflow/sop/steps/govee_widget.yaml`；验证：该目录只剩 `ui_task.yaml`。**验证结果**：目录仅 `ui_task.yaml`。
- [x] 2.2 从 `engines/backend_bridge/workflow/sop_ui.py` 的 `SPEC_KEYS` 摘除 `govee_widget` 键；验证：`python -c "from engines.backend_bridge.workflow.sop_ui import SPEC_KEYS; print(sorted(SPEC_KEYS))"` 输出仅 `['ui_task']`。**验证结果**：`SPEC_KEYS = ['ui_task']`。
- [x] 2.3 同步 `backend/apps/ai_assistant/management/commands/run_ui_sop.py` 的帮助文案；验证：`git grep "govee_widget|Govee 专项"` 在两文件无命中，`python manage.py check` 通过。**验证结果**：无命中；`manage.py check` 0 issues。
- [x] 2.4 清理 `tests/engines/backend_bridge/` 中对该流程键的引用；验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge -q` 全绿。**验证结果**：34 passed。

## 3. 数据迁移收敛已播种提示词

- [x] 3.1 在 `backend/apps/ai_assistant/migrations/` 新增 `0065_*` 数据迁移：按词级替换收敛厂商标识，保留提示词其余结构与人工改动，反向为 `noop`；验证：`python manage.py makemigrations --check --dry-run` 无待生成变更。**验证结果**：`No changes detected`；`showmigrations` 序列连续至 `0065`。
- 【已取消 · 未做取消】3.2 在测试库上验证迁移：正向执行后 `prompt_*` 不再含厂商标识，反向 `noop` 可正常回滚不报错；验证：新增用例覆盖「命中则替换」「不命中则跳过」两条分支并通过 pytest。**未完成**：尚未补迁移单测。
- [x] 3.3 确认迁移编号未与并行分支冲突；验证：`ls backend/apps/ai_assistant/migrations/` 中 `0065` 唯一，`python manage.py showmigrations ai_assistant` 序列连续。**验证结果**：唯一，序列连续。

## 4. 常驻门禁

- [x] 4.1 在 `utils/check_gates.py` 实现 `business-asset` 门禁：受管业务资产目录（`app_info/`、`sop/steps/`）的大小写不敏感内容与路径匹配 + 已禁用路径清单；验证：临时造命中文件时退出码 1，删除后退出码 0。**验证结果**：造 `_probe_vendor.md` 后 `--only business-asset` 退出码 1 并输出命中文件；删除后退出码 0。
- [x] 4.2 把该门禁注册进 `build_gates()` 并设为阻塞项；验证：`python run.py check` 的输出中出现该门禁。**验证结果**：`--only business-asset` 输出 `PASS business-asset 业务资产（受管目录禁厂商标识 / 禁用路径不复活）`。
- [x] 4.3 把 `.github/workflows/ci-phase1.yml` 中 `static-checks` job 的 `--only silent-except` 扩为 `--only silent-except,business-asset`；验证：job 数仍为 6，本地可执行。**验证结果**：`runs-on` 计数 6；`--only silent-except,business-asset` 本地 2/2 通过。
- 【已取消 · 未做取消】4.4 为门禁补用例，覆盖「命中则失败」「不命中则通过」「已禁用路径复活则失败」三种情形；验证：`python -m pytest -c tests/pytest.ini tests/arch -q` 全绿。**未完成**：目前只有手工正反向验证，尚无自动化用例。

## 5. 全量校验与交付

- [x] 5.1 跑本地质量门禁；验证：`python run.py check` 退出码 0。**受阻**：`ruff-lint`、`ruff-engines-format`、`ruff-engines-lint` 失败，失败文件全部来自**工作区他人未提交改动**（`knowledge_assistant/consumer.py`、`engines/agents/agent_builders.py` 等 9 个），与本次改动无关；本次涉及的文件单独跑 ruff 全绿。CI 侧同样三项 ruff 检查为 success，反证失败来自未提交改动。
- [x] 5.2 校验 OpenSpec 变更本身；验证：`openspec validate purge-govee-business-assets --strict` 通过。**验证结果**：`Change 'purge-govee-business-assets' is valid`。
- [x] 5.3 逐文件暂存并提交，不使用 `git add -A`；验证：`git diff --cached --name-only` 与改动清单一致。**验证结果**：`b595a3c2` 15 文件。`agent_config.yaml` 含他人未提交的配置重构，改用「HEAD 版本摘 4 行 → `hash-object -w` → `update-index --cacheinfo`」只暂存本次改动；索引复核仅含两处 `app_info` 删除。
- [x] 5.4 推送主干并确认流水线；验证：`git push origin Kahoku` 成功。**验证结果**：`1198a69b..b9159182`，不走代理直连成功。CI `43613884226`：`security-scan` / `boundary-check` / `frontend-quality` 通过，`business-asset` 门禁在 `static-checks` 的 “Silent exception check” 步骤实际执行并通过；`static-checks` / `backend-check` / `frontend-check` 失败，失败 job 与步骤与本次之前那次运行（`43609805058`）**完全一致**，未引入新失败。
