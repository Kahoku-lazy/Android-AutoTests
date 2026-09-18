## 1. 复核（实测，已完成）

- [x] 1.1 全仓扫 `apps/**/views*.py` 的直写模式 → **0 命中**
- [x] 1.2 正对照：同一检测口径对 `apps/evaluator/api.py` → 14 处命中（检测器有效，不是「扫描坏了才 0 命中」）
- [x] 1.3 逐个读 4 个「可疑」文件，确认其写方法都显式调 api：
      `element_locator/views_projects_drf.py`（`ViewSet` ×2，项目写方法 `raise MethodNotAllowed`）·
      `case_manager/views_drf.py`（`ViewSet` ×4 全调 `case_api`）·
      `workflow/views_api.py`（6 个 `perform_*` 全调 `wf_api`）·
      `ai_assistant/views_drf.py`（`GenericViewSet` 无 mixin，自定义 `action` 调 `api`）
- [x] 1.4 确认上一单续做清单「其余 App 的 ViewSet 隐式写」是**误判** —— 它按「有没有覆写 `perform_*`」推断，
      而 `viewsets.ViewSet` / `GenericViewSet` 根本没有隐式写方法
- [x] 1.5 确认 `viewsets.*` 定义共 20 个，**全部**位于 `views*.py` 文件内 → 通配发现覆盖 100%
- [x] 1.6 确认 `tools/gen_arch_stats.py --check-boundaries` 只覆盖防火墙 #2（跨模块 ORM 写），
      不覆盖「View 写本 App 模型」；`calibration.md` §7 该条为**手工** `rg` → 存在门禁缺口

## 2. 修改

- [x] 2.1 新增 `tests/arch/test_view_write_convergence.py`（119 行）：`ast` 检测器 `find_orm_writes`
      + 逐模块参数化断言 `test_view_module_has_no_direct_orm_write`（当前 24 个 `apps/*/views*.py`）
- [x] 2.2 同文件内加正对照 `test_detector_flags_known_violations` + 范围自检 `test_view_modules_discovered`
- [x] 2.3 模块 docstring 声明判据（无条件 vs 需 `objects`）与**未覆盖**场景（关系管理器 M2M 写）
- [x] 2.4 `ruff format` 归位（`frozenset` 字面量被折叠）

## 3. 验证

- [x] 3.1 `pytest tests/arch -q` → **32 passed**（既有 `test_channels.py` 6 + 本守卫 26）
- [x] 3.2 **守卫可失败实测**：写入 `apps/evaluator/views_zz_probe.py`（含 `instance.delete()`）→
      `FAILED test_view_module_has_no_direct_orm_write[views_zz_probe.py]`，
      报错文案 `views_zz_probe.py 直接写 ORM，应改为调用本 App api.py：L5 instance.delete`；
      删除该文件后 `Test-Path` → `False`，重跑 26 passed → 守卫不是「永远绿的假门禁」
- [x] 3.3 `python -m ruff check .` → All checks passed!；
      `python -m ruff format --check .` → 261 files already formatted
- [x] 3.4 `python manage.py check` → System check identified no issues (0 silenced)
- [x] 3.5 `pytest tests/graybox/unit tests/arch -q` → **211 passed**（= 改动前 185 + 本单 26）

## 4. 归档

- [x] 4.1 diff 范围：仅新增 `tests/arch/test_view_write_convergence.py`（119 行，无生产代码改动）；
      实测证据：注入违规 → 1 failed（含文件:行:调用名）；撤回 → 32 passed
- [x] 4.2 `openspec archive add-view-write-convergence-guard -y --json` → 归档为 `2026-09-15-add-view-write-convergence-guard`（`specsUpdated: false`）

## 5. 续做（不在本单）

- 同口径守卫扩展到 `consumers*.py`（WS 推送层）与 Tool 层
- 经实例关系管理器写 M2M 的静态检测（需类型推断，AST 不可判）
- `api.create_eval_run` 收 ORM 实例做参数（calibration §6 规则 5 偏差）
- `GET /runs/{id}/` 的 `results` 取数口径（`converge-evaluator-drf-writes` 遗留）
