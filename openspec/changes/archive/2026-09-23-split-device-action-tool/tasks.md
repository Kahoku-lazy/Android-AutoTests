## 1. 后端：拆解工具

- [x] 1.1 `apps/ai_assistant/tools.py` 删除 `device_action`，新增 6 个单职责函数（`app_control` / `tap_screen` / `swipe_screen` / `press_key` / `input_text` / `current_app`），逐条迁移原 8 分支的参数守卫（package 必填、x/y 非 0、未知动作报错），`current_app` 只读且只取 `engine.app_current()`，验证：`python -m ruff check apps/ai_assistant/tools.py` 通过，且模块内不再出现 `device_action`
- [x] 1.2 同步注册表四处：`TOOLS`（5 个写 + `current_app` 只读）、`TOOL_META`（6 个互不重复的 action）、`AUTO_ALLOW_TOOLS`（替换原 `device_action` 为 5 个写工具）、`DEBUG_PARAM_OPTIONS`（6 个 `serial` 候选），验证：新增用例断言 6 个新工具均存在、`current_app.read_only is True`、其余 5 个为 False，且 `device_action` 已不在 `TOOLS`/`TOOL_META`
- [x] 1.3 `engines/ai/agentscope/config.py` 的 `VISION_TOOLS` 用 6 个新名替换 `device_action`，验证：`python -m ruff check engines/ai/agentscope/config.py` 通过，且 `VISION_TOOLS` 中每个名字都存在于 `TOOLS`（新增断言）

## 2. 提示词同步（DB 数据）

- [x] 2.1 更新 `apps/ai_assistant/migrations/0038_aiagent_device_prompts.py` 中 executor 的两处短语（swipe / input_text 改用新工具名），验证：该文件内不再出现 `device_action`
- [x] 2.2 新增 `apps/ai_assistant/migrations/0040_*.py`：对 `ai_agents.prompt_executor` 做短语级条件替换（不含原文短语则跳过），reverse 反向还原，验证：`python manage.py makemigrations --check --dry-run` 无遗漏；迁移后存量库提示词不含 `device_action`，且新值 `== 旧值.replace(原文, 新文)`（证明外科式替换、其余内容未动）

## 3. 手册、常量与文档（工具名层面）

- [x] 3.1 `engines/ai/skills/platform-tools-manual/SKILL.md`：把 `device_action` 一行换成 6 行；总数 12 → **17**；重写推荐序列 ③、关键入参段、写操作铁律清单、frontmatter description（分类归属在 §4 重组），验证：手册内不再出现 `device_action`
- [x] 3.2 `frontend/src/modules/ai-assistant/constants.ts` 的 `PLATFORM_TOOL_NAMES` 与模块 `AGENTS.md` 的设备候选工具清单同步为 6 个新名，验证：`cd frontend && npm run typecheck` 通过，且两文件内不再出现 `device_action`
- [x] 3.3 `dev_docs/DEV_TEST/接口文档/API-AI助手.md`：schema 示例的工具名改为新工具，候选工具口径清单同步，验证：文档内不再出现 `device_action`

## 4. 分类重组（按性质，4 类 → 6 类）

- [x] 4.1 `apps/ai_assistant/tools.py` 的 `TOOL_CATEGORIES` 扩到 6 类（设备管理 📱 `#6BCB77` / 设备控制 🎮 `#F7C948` / 设备信息 📋 `#4ECDC4` / 设备检查器 📸 `#FFB5A7` / 视觉识别工具 🔍 `#A78BFA` / 工作流 🧭 `#38BDF8`），`TOOL_META` 按性质重挂 10 个工具（台账 3 / 控制 8 / 信息 2），验证：`python -m ruff check apps/ai_assistant/tools.py` 通过，且分类色互不重复
- [x] 4.2 `engines/ai/skills/platform-tools-manual/SKILL.md` 总览改为 6 类（3/8/2/1/1/2 = 17）并同步 description 与链路归属，验证：手册内各分类条目数之和等于标题数字
- [x] 4.3 `dev_docs/DEV_TEST/接口文档/API-AI助手.md` 的 available-tools 示例补上拆分后的分类，验证：示例分类清单与 `TOOL_CATEGORIES` 一致
- [x] 4.4 分类「工作流」改名为「页面流工具」（`TOOL_CATEGORIES` 键 + `TOOL_META` 两处 + 手册总览/description + 接口文档 6 类说明 + 分类断言 + design 表），验证：`python -m pytest tests/graybox/unit/test_ai_platform_tool_debug.py -q` 通过，且 `TOOL_CATEGORIES` 内键为「页面流工具」

## 5. 测试与 spec 同步

- [x] 5.1 `tests/graybox/unit/test_ai_platform_tool_debug.py`：`_PHONE_TOOLS` 改为拆分后的 9 个需要 serial 的工具；schema/调用用例改用 `tap_screen`；补断言 `device_action` 已从 schema 与 available-tools 清单消失，验证：`python -m pytest tests/graybox/unit/test_ai_platform_tool_debug.py -q` 通过
- [x] 5.2 补分类断言用例（6 类清单与顺序、分类色互不重复、「设备控制」恰为会在手机上产生副作用的 8 个、台账/信息类不含控制类工具、每个工具恰属一个已登记分类且无孤儿），验证：`python -m pytest tests/graybox/unit/test_ai_platform_tool_debug.py tests/graybox/unit/test_inspector_ocr_tool.py -q` 通过
- [x] 5.3 `frontend/tests/ai-assistant/p0/useToolDebug.spec.ts`（改用 `swipe_screen`）与 `ToolDebugPage-device-options.spec.ts`（改用 `tap_screen`），验证：`cd frontend && npx vitest run tests/ai-assistant` 通过
- [x] 5.4 spec delta 已把三处要求的样例工具改为 `tap_screen`，并把候选要求改为按性质描述（不再写「设备管理分类下」），验证：`openspec validate split-device-action-tool --strict` 通过

## 6. 一致性校验、门禁与真机抽验

- [x] 6.1 全仓检索 `device_action`，确认仅剩允许命中（本变更产物、新迁移必须保留的原文短语、历史归档），验证：`git grep -n device_action` 输出逐条可解释
- [x] 6.2 后端门禁：`python manage.py check`、`python -m ruff check`（改动文件）、`python -m pytest tests/graybox/unit -q`、`python tools/gen_arch_stats.py --check-boundaries`，验证：全部通过、边界零违规
- [x] 6.3 前端门禁：`cd frontend && npm run lint:styles && npm run typecheck && npx vitest run tests/ai-assistant`，验证：全部通过，无新增 vue-tsc 错误
- [x] 6.4 真机抽验（设备 `R5CT62RH88F`）经 HTTP invoke：`current_app` → **200** `{package, activity, pid}`；`tap_screen` 缺坐标 → **400**（"click 需要 x/y 坐标"）；`app_control` 坏动作 → **400**；`device_action` → **404**。**偏差**：未发真实点击（避免无谓改动设备状态；点击分支与原 `device_action` 逐行一致，且参数守卫生效已证明）
