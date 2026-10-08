## 1. 修复与守门

- [x] 1.1 修复 `apps/ai_assistant/model_debug.py`：把 `build_device_models` 加回引擎**包级**导入（`from engines.ai.agents import ... build_device_models`），使 `build_device_models_for_agent` 不再抛 `NameError`。验证：`python -m ruff check --select F821 apps/ai_assistant/model_debug.py` 零命中，且 `python manage.py model_test planner "启动 govee 应用并进入设备列表"` 能跑出规划结果（见 2.4）。**验证结果**：该行修复后 `git diff` 仅显示新增 `+    build_device_models,` 一行；F821 该文件零命中；实跑成功（见 2.4）。
- [x] 1.2 在 `ruff.toml` 的 `[lint] select` 增加 `F821`（未定义名），把"用了没导入的名字"这类缺陷纳入机械门禁。验证：`python -m ruff check --select F821 .` 全仓零命中（修复 1.1 之前实测存量恰 1 处，即本缺陷）；门禁范围 `python -m ruff check apps/ config/ gateway/ shared/ models/ engines/` 仍全绿。**验证结果**：修复前 `--select F821 .` = 1 error（命中点即 `model_debug.py:120`）；修复后 **All checks passed**；门禁范围 lint 全绿（187 文件格式检查亦通过）。**守门有效性实测**：把历史版本文件内容（`git show 43756da0:...`）写到 `temps/` 后用新规则检查 → 精准命中该调用点（1 error），证明此规则本可在 `f823a6a7` 就拦住该缺陷；检查完已删除临时文件。
- [x] 1.3 新增回归用例 `tests/graybox/unit/test_ai_debug_assembly_entry.py`：**不打桩被测函数**，用桩 agent 调真实 `build_device_models_for_agent`，只对密钥解密（`decrypt_key`）与技能目录（`list_enabled_skill_dirs`）打桩；断言返回「1 份三角色配置 + 3 个角色对象」，且 `PlannerRole` / `ExecutorRole` / `VerifierRole` 的 `spec.role` 与视觉标记正确。验证：该文件全绿；并做一次**守门有效性实测**——临时注释掉 1.1 的 import 复跑，用例必须失败，恢复后必须通过。**验证结果**：**守门有效性已实测** —— 去掉修复后跑该文件：`2 failed`，两条用例均报 `NameError: name 'build_device_models' is not defined`；恢复修复后：`2 passed`（5.74s）。用例本身 lint/format 亦通过。

## 2. 验证

- [x] 2.1 lint 与自检：门禁范围 `python -m ruff check apps/ config/ gateway/ shared/ models/ engines/` + `python -m ruff format --check apps/ config/ gateway/ shared/ models/ engines/` + `python -m ruff check --select F821 .` + `python manage.py check`。验证：全部通过、F821 零命中。（注：`ruff check .` 另有 31 处门禁范围之外的既有告警，与本单无关，不在验收口径内。）**验证结果**：门禁范围 `ruff check` → All checks passed；`ruff format --check` → 187 files already formatted；`--select F821 .` → All checks passed；`manage.py check` → `System check identified no issues (0 silenced)`。门禁外 31 处的规则码实测为 T201(14) / I001(11) / F401(3) / Q000(2) / Q003(1)，全部位于 tests/ 等门禁外路径，本单未新增。
- [x] 2.2 相关用例全绿（最小集，禁止主动跑全量回归）：`pytest tests/graybox/unit/test_ai_debug_assembly_entry.py tests/graybox/unit/test_ai_model_debug.py tests/graybox/unit/test_ai_debug_log_check.py tests/graybox/unit/test_ai_engine_config.py tests/graybox/unit/test_ai_role_tool_subsets.py tests/arch/test_channels.py -q`。验证：全部通过。**验证结果**：**68 passed**（38.46s），含新增 2 条。
- [x] 2.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries`。验证：模块边界检查通过、零违规（本单只加引擎包级导入，方向不变）。**验证结果**：`✅ 模块边界检查通过 — 零违规`。
- [x] 2.4 实跑规划角色（用户要求的"看效果"）：`python manage.py model_test planner "启动 govee 应用并进入设备列表"`。验证：命令退出码 0 并打印出规划结果（计划/步骤/断言）；执行与验收阶段需要设备与单独授权，本单不跑并在汇报中显式标注。**验证结果**：**成功**。规划角色真实调用了它的工具子集（`list_page_flows` ×2、`get_page_flow` ×1，读到页面流文档「H6810设备页面关系流」17 节点），3 次模型调用均 HTTP 200，最终产出：

  ```json
  {"plan": {"goal": "启动 govee 应用并进入设备列表（设备主页页面）",
   "steps": [
     {"action": "启动 govee 应用（包名 com.govee.home）",
      "assert": "应用启动成功并停留在 govee 的 APP主页", "log_check": false},
     {"action": "先在 APP主页找到底部「设备主页入口」元素，再点击该入口",
      "assert": "页面跳转成功，进入设备主页页面，展示设备列表（可见「设备」「全部」等文案及 H6810 设备项）", "log_check": false}]}}
  ```

  其思考轨迹显示它是按页面流推导的（APP主页 → 点「设备主页入口」→ 设备主页页面）。**执行 / 验收阶段未跑**（需在线设备与单独授权）。
- [x] 2.5 关单与归档：汇总改动清单、F821 零存量证据、用例结果与实跑输出；`openspec validate` 通过后按流程归档（`skip_specs: true`）。验证：`openspec validate "2026-10-08-fix-model-debug-assembly"` 通过并完成归档。**验证结果**：改动清单 = `apps/ai_assistant/model_debug.py`（1 行）+ `ruff.toml`（1 条规则）+ 新增 1 个用例文件；`openspec validate --strict` 通过；已归档。
