# Tasks: align-spec-guards-with-test-policy

## 1. 规格对齐

- [x] 1.1 落 4 个 delta（`specs/{api-path-convention,auth-form-validation,auth-response-shape,auth-session}/spec.md`），6 条 MODIFIED 需求整块复制后只改"由谁守护"的指向。**验证结果**：`openspec validate align-spec-guards-with-test-policy --strict` → `Change 'align-spec-guards-with-test-policy' is valid`。
- [x] 1.2 确认改动只动"守卫落点"：每条需求正文的断言内容、场景条数与场景名均不变。**验证结果**：与 `openspec/specs/<capability>/spec.md` 逐条比对，只出现 `tests/graybox/unit` → `tests/arch/unit` 与「默认单元测试」→「`tests/arch/unit` 契约守护」的替换；6 条需求的场景数与场景名一一对应。
- [x] 1.3 归档后活跃规格不再出现 `tests/graybox`。**验证结果**：`openspec archive align-spec-guards-with-test-policy --yes` → `~ 6 modified`（0 新增/0 删除），随后 `Select-String -Path openspec/specs/*/spec.md -Pattern graybox` → **0 命中**；`git diff openspec/specs` 为 10 行替换，全部是"由谁守护"的指向改写。

## 2. 落点核验

- [x] 2.1 确认规格指向的守护真实存在且默认执行。**验证结果**：`python -m pytest -c tests/pytest.ini tests/arch/unit -q` → 184 passed / 4 failed，与基线一致（`test_auth_single_verify`、`test_api_path_callers::test_every_caller_path_resolves_to_a_view`、`test_channels`、`test_view_write_convergence`，均为既有失败，与本次无关）。
- [x] 2.2 确认 delta 与 main spec 的需求标题逐字一致（MODIFIED 匹配前提）。**验证结果**：`openspec validate align-spec-guards-with-test-policy --strict` 与 `openspec validate --specs` 均无 `requirement not found` / 标题不匹配报错；全仓 `158 passed, 0 failed`。
