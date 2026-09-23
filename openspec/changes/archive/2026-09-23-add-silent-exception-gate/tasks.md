## 1. 口径确认与基线

- [x] 1.1 实测三种口径的命中量：全量"无 raise 且无日志"183 处 → 加"直接返回默认值"49 处 → 仅"处理器体为空"18 处，据此定为最窄口径（理由见 design.md 决策 1）
- [x] 1.2 拆分 18 处的归属：供应商产物 10 处、历史迁移 1 处、**项目自有 8 处**

## 2. 实现门禁

- [x] 2.1 `tools/check_gates.py` 新增 `silent_except_gate()`：AST 判定 `except` 处理器体是否为单一 `pass`/`continue`/`break`，且无 `raise`、无日志调用、无注释
- [x] 2.2 排除范围：`engines/ai/skills/skill-creator/**`（与 `ruff.toml` 一致）与 `**/migrations/**`（历史迁移不可改）——首次运行时因未排除迁移命中 1 处，已修正
- [x] 2.3 解析失败的文件输出为一条违规（不静默跳过）
- [x] 2.4 登记到检查清单，级别为**告警**（`blocking=False`）

## 3. 清理存量（8 处，纯注释）

- [x] 3.1 `apps/ai_assistant/rag_service.py:70` — 删除为幂等操作，集合不存在或后端不可用时无影响
- [x] 3.2 `apps/ai_assistant/skills_catalog.py:57` — 单文件取不到大小时跳过，体积统计按尽力而为
- [x] 3.3 `apps/ai_assistant/views/tool_gateway.py:65` — 预期未命中：PK 落空后继续按 UUID 查
- [x] 3.4 `apps/device_inspector/service.py:163` — 取不到前台应用时 package/activity 保持空串（可选元数据）
- [x] 3.5 `apps/device_pool/api.py:130` — 设备不存在即视为释放失败返回 False，属契约内正常分支
- [x] 3.6 `apps/device_pool/manager.py:139` — 本轮 adb 取值失败交由下方重试，重试耗尽由调用方按空值处理
- [x] 3.7 `config/settings.py:16` — django-stubs-ext 为可选开发期依赖
- [x] 3.8 `engines/ai/agentscope/model.py:52` — 本函数遍历多段文本，非 JSON 片段跳过即可

## 4. 验证

- [x] 4.1 单独运行 `silent-except` 门禁：**0 命中**（修复前 8 处）
- [x] 4.2 `ruff check` 覆盖 `tools/check_gates.py` 与 8 个被改文件：通过；`ruff format --check` 对 `tools/check_gates.py`：已合规
- [x] 4.3 `python manage.py check`：通过（确认注释插入未破坏语法）
- [x] 4.4 人工核对：8 处改动**全部是新增注释**，无任何语句增删（`git diff` 逐处确认）

> **验证范围说明**：按 `AGENTS.md` 测试范围收敛条款，未运行 `python run.py check` 全量与 `pytest tests/`；本变更改动仅为注释与新增检查，用"该门禁自身 + ruff + manage.py check"作为最小集。

## 5. 收尾

- [x] 5.1 记录已知未覆盖类别：`except X: return <默认值>` 共 31 处不判违规（理由与后续路径见 design.md 决策 2）

---

## 结果记录（2026-09-23）

| 项目 | 实施前 | 实施后 |
| --- | --- | --- |
| `silent-except` 门禁命中 | 项目自有 **8 处** | **0** |
| 供应商产物 / 历史迁移 | 10 处 / 1 处 | 按范围排除，未改动 |
| 运行期行为 | — | 零变化（8 处均为新增注释） |
| 门禁级别 | — | 告警（转拦截由后续变更执行） |
