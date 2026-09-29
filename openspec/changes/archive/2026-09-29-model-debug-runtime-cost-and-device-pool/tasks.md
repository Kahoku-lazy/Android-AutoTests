## 1. 前端：取消调试对话的固定等待上限

- [x] 1.1 `frontend/src/modules/ai-assistant/api/toolbox.ts`：`chatWithModelDebug` 改为显式声明不设等待上限（axios 语义 `timeout: 0`），不再沿用共享客户端的默认上限；其余接口不受影响。验证：`frontend/tests/ai-assistant/p0/useModelDebug.spec.ts` 的请求契约断言改为"第三个参数显式声明不设上限"（`expect(post.mock.calls[0]).toHaveLength(3)`），用例通过
- [x] 1.2 `frontend/src/modules/ai-assistant/constants.ts` + `ModelDebugPage.vue`：范围说明补"不提供中止：跑飞的调试只能刷新页面，且刷新不会中止后端本轮执行"，与"不设上限"配套如实描述。验证：用例断言该文案在页面上可见（`MODEL_DEBUG_SCOPE_NOTE`），且页面不出现「不挂工具 / 不碰真机 / 单次最长 5 分钟」

## 2. 前端：费用展示（本轮 + 会话累计）

- [x] 2.1 `frontend/src/modules/ai-assistant/composables/useModelDebug.ts`：新增 `sessionCost` / `hasSessionCost`（仅内存；清空对话与切换角色后归零；某轮未返回费用时该轮不计入）。验证：新增用例覆盖"两轮累加 = 两轮之和""无费用轮次不显示且累计不出现""清空后累计消失"
- [x] 2.2 `frontend/src/modules/ai-assistant/ModelDebugPage.vue` + `ModelDebugPage.style.css` + `constants.ts`：每条助手回复内显示本轮费用（`data-testid="model-debug-msg-cost"`），对话栏显示会话累计（`data-testid="model-debug-session-cost"`），费用格式复用既有 `formatTaskCost`（单一真相源）；未返回费用时如实不显示。验证：用例断言两个展示点文案与数字正确、无费用时元素不存在；**因页面加到 498 行逼近 500 行门禁，同批把轨迹展示的纯函数拆到 `helpers/model-debug-trace.ts`，页面降到 485 行**

## 3. 后端：调试对话不装配设备池记账工具

- [x] 3.1 `apps/ai_assistant/model_debug.py`：新增 `DEVICE_POOL_ACCOUNTING_TOOLS` 与 `debug_tool_names()`，`build_debug_role` 按它装配；生产角色规格与生产装配不动。验证：`tests/graybox/unit/test_ai_model_debug.py::test_debug_subset_excludes_device_pool_accounting_tools` 断言两个名字被排除、其余一个不少，且这两个名字确实属于执行角色生产子集
- [x] 3.2 该角色"是否需要设备"与二次确认的写工具数量随实际子集成立：`role_needs_device` 改走 `debug_tool_names()`；只读配置逐工具加 `debug_mounted`；前端写工具计数只数 `debug_mounted` 的。验证：后端 `test_config_marks_debug_mounted_tools`（清单仍与角色规格逐名一致、两个记账工具标 false）与 `test_role_config_declares_needs_device` 通过；前端用例断言记账工具行标「调试不挂载」且确认框仍写「2 个写工具」（不含被排除者）

## 4. 规格与关单

- [x] 4.1 把本单 delta 同步进主规格（「调试对话按该角色真实装配运行」补例外与场景、「需要设备的角色须先选定设备并获得一次性授权」改由不装配兑现并明确写工具计数口径、「调试对话不设前端等待上限且如实描述行为」明确显式取消默认上限并如实标注不提供中止、新增「调试对话展示本轮与会话累计费用」）。验证：`openspec validate "2026-09-29-model-debug-runtime-cost-and-device-pool" --strict` 通过；`openspec validate --specs` 无 ✗
- [x] 4.2 门禁：后端 `python manage.py check`（no issues）、`python -m ruff check` + `ruff format --check`（All checks passed）；前端 `npx vue-tsc --noEmit`（无输出）、`npx eslint src/modules/ai-assistant`（0 error）、`npx prettier --check`（改动文件全部符合）。验证：上述命令输出全绿
- [x] 4.3 相关用例收口：前端 `npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts tests/ai-assistant/p0/model-debug-log-check.spec.ts` → 46 passed；后端 `python -m pytest tests/graybox/unit/test_ai_model_debug.py -q` → 21 passed。验证：两处均全绿，无失败项
