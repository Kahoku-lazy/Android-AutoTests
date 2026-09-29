## 1. 后端：参数中文名与说明

- [x] 1.1 在 `apps/ai_assistant/tools.py` 增加参数标签表 `PARAM_LABELS`（参数名 → 中文短名）与 `TOOL_PARAM_LABELS`（工具级覆盖），覆盖现有全部工具的参数（`serial`/`text`/`xpath`/`action`/`keyword`/`at`/`port`/`seconds` 等），验证：单测断言每个已登记参数 `label` 非空且不等于英文名
- [x] 1.2 实现 docstring `Args:` 段解析（含续行合并），产出 `hint`，验证：单测用 `read_device_log` 的 docstring 断言 `keyword` 的 `hint` 非空、未写说明的参数 `hint` 为空串
- [x] 1.3 `get_tool_debug_schema` 下发 `label` / `hint`（未登记回退英文名、说明缺失为空串），验证：单测断言字段存在、回退与空值口径正确，且参数列表仍不含 `user_id`
- [x] 1.4 确认既有字段与行为不变（`type` / `required` / `default` / `options_source` / 候选清单），验证：既有 `test_ai_platform_tool_debug.py` 全绿
  - 顺带修掉一条既有断言：上一变更（add-device-log-read-tool）新增「设备日志」分类后，`test_tool_categories_group_tools_by_nature` 的分类清单未同步（当时漏跑这条测试），现已补 6 → 7 与成员断言

## 2. 前端：标签渲染

- [x] 2.1 `frontend/src/modules/ai-assistant/api/toolbox.ts` 的参数 DTO 增加 `label` 与 `hint` 字段，验证：`npx vue-tsc --noEmit` 通过（无类型缺口）
- [x] 2.2 `ToolDebugPage.vue` 参数标签改为「中文名（english_name）」+ 必填/可选 + 类型，英文名保留可见，验证：页面渲染形如「日志关键词搜索（keyword） 可选 str」
- [x] 2.3 `hint` 以悬浮提示（`title`）呈现，不铺开表单，验证：页面上参数说明不在正文占行，鼠标悬停可见
- [x] 2.4 样式只用 `tokens.css` 字号令牌，验证：`npx eslint src/modules/ai-assistant` 0 error、`npx prettier --check` 通过、`vue-tsc` 通过
- [x] 2.5 `frontend/src/modules/ai-assistant/AGENTS.md` 补一句参数标签口径（中文名 + 英文名 + 必填/可选 + 说明走提示），验证：文档行与实现一致

## 3. 验证与收口

- [x] 3.1 后端单测覆盖 specs 每条 Scenario（label/hint 下发、回退、docstring 解析、候选清单不变、无 `user_id`），验证：`pytest tests/graybox/unit -k "tool_debug"` 全绿（37 条）
- [x] 3.2 前端契约对拍（Python 侧读源码）：断言调试页模板使用 `paramLabel(p)`、保留 `p.required`/`p.type`、说明走 `:title="p.hint"`、DTO 声明 `label`/`hint`、调试页与标签函数不硬编码中文名，验证：`test_tool_debug_param_labels_contract.py` 全绿（5 条）
- [x] 3.3 门禁：`python manage.py check`、`ruff check apps/ config/ engines/`、`python tools/gen_arch_stats.py --check-boundaries` 通过；前端 `vue-tsc` + `eslint`（0 error）+ `prettier` 通过
- [x] 3.4 页面确认：起平台后打开 `read_device_log` 调试页，验证：四个参数显示为「中文名（english）」且逐个带「可选」，说明可悬停查看
  - 实测（Playwright 打开 `/ai-assistant/toolbox/tools/read_device_log`，截图 `temps/tool_debug_page.png`）：
    - `日志时间点（at） 可选 str`
    - `查询跨度（秒）（seconds） 可选 float`
    - `日志端口（port） 可选 int`
    - `日志关键词搜索（keyword） 可选 str`
    - 每个字段的 `title` 均为对应中文说明（悬停可见，表单正文不铺开）
