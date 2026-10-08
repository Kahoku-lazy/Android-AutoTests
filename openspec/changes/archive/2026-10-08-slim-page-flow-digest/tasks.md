## 1. 摘要瘦身与诊断保全

- [x] 1.1 `apps/workflow/semantics.py::build_graph_digest`：节点摘要不再写入 `elements` 与 `navigation_entries`（其余字段一律保留）。验证：以合成 config 构建摘要，节点条目不含这两个键。**验证结果**：节点条目不再输出两者（新用例 `test_nodes_have_no_element_inventory` 断言全部 3 个节点均无）；模块 docstring 同步改为"输出页面与节点关系"，并写明"MUST NOT 输出页面元素清单"。
- [x] 1.2 把「连线端口槽位不可解析」的告警改到连线遍历处产生（入 `warnings` 前去重，避免与弹窗路径重复）。验证：构造一条 `origin_slot` 非法的连线，断言 `parse_warnings` 仍记录该问题，且同一连线只记一次。**验证结果**：新用例 `test_unparsable_slot_still_warns_once` 断言恰好 1 条且含连线 id；口径精化为"**有值但不可解析**才告警"（避免对未设槽位的连线误报），已在代码注释写明。
- [x] 1.3 删除随之零引用的 `_collect_elements` 与 `_element_source`（`_resolve_port_targets` 保留：弹窗 `close_returns_to` 仍用）。验证：grep 两函数在全仓零引用后删除；删除后相关用例全绿。**验证结果**：删除前 grep `apps/workflow/*.py` 确认 `_collect_elements` 仅被自身定义处引用、`_element_source` 仅被它引用；删除后 **F821（未定义名）通过**、全仓 grep 两名字 **零命中**；`_resolve_port_targets` 保留（弹窗路径仍用）。

## 2. 执行提示词收口

- [x] 2.1 `engines/ai/agents/config.py` 的 `VISION_PROMPT`：三处与能力不符的表述改为一致口径——① 视觉定位优先（元素 xpath 仅在步骤明确给出时使用）；② 页面内元素操作那条删去"若页面流中已有该元素优先用其 xpath"；③ "按页面流的跳转边逐页推进"改为"按步骤推进到测试点"。工具清单、截图铁律与 `xpath_action` 用法不动。验证：grep 该提示词内不再出现"页面流"；提示词其余段落逐字未改。**验证结果**：`VISION_PROMPT` 内"页面流" **零命中**；全文件仅剩两处在**规划**提示词与其注释（规划确有那两个工具，正确）。`xpath_action` 的用法描述未动（仍支持"步骤给出 xpath"与人工传入的场景），SOP 段与截图铁律逐字未改。

## 3. 评测口径收敛

- [x] 3.1 `tests/ai_planner/cases/planner.yaml` 只留 `single-step` 与 `multi-step`；其余 5 条移入新增的 `tests/ai_planner/cases/extended.yaml`（同格式）。文件头写明正式口径：**只用 deepseek-flash、只跑这两条**；扩展文件标注"按需指定，不默认跑"。验证：`load_cases` 读主文件得 2 条、读扩展文件得 5 条。**验证结果**：主文件 2 条、扩展文件 5 条（named-device / with-attachment / json-four-keys / log-check-step / vague-demand），两个文件头都写明了口径与用法。
- [x] 3.2 评测单测补口径守卫：断言主用例集恰为 2 条且 id 为 `single-step` / `multi-step`（防止误改口径），并断言扩展文件可独立加载。验证：用例通过；把主文件改回 7 条即红。**验证结果**：新增 `test_committed_case_files_match_agreed_scope`（断言主文件 id 序列、扩展文件 ≥5 条、两文件不重复）→ 通过。

## 4. 测试与规格

- [x] 4.1 新增 `tests/graybox/unit/test_workflow_page_flow_digest.py`（纯函数、无库无模型）：① 节点无 `elements`/`navigation_entries`；② 连线保留 `from_port_name`（可命名点击目标）；③ `paths` 仍产出；④ 起点节点仍只输出 `start_kind`/`package_name`（守住既有规格）；⑤ 槽位不可解析的连线仍进 `parse_warnings`。验证：全绿；把 `elements` 塞回即红。**验证结果**：**6 项全绿**（并额外覆盖"出入关系保留"与"坏输入容错"）；该摘要此前**零测试覆盖**，本次一并补上。
- [x] 4.2 规格 delta（`ai-device-planner-tools`，ADDED 一条需求）：规划读取的摘要只含页面与节点关系，MUST NOT 输出元素清单；含"仍可命名点击目标"与"诊断不退化"两个场景。验证：`openspec validate` 通过、归档时新增成功（既有两条需求原文保留）。**验证结果**：validate --strict 通过；归档时 `+ 1` 新增、既有需求未动。

## 5. 验证

- [x] 5.1 相关用例最小集：新增摘要用例 + `test_ai_planner_eval.py` + `test_ai_role_tool_subsets.py` + `test_ai_engine_config.py` + `tests/arch/test_channels.py`。验证：全绿（不发起全量回归）。**验证结果**：**59 passed**（6.33s）。
- [x] 5.2 后端自检与静态检查：`python manage.py check` + 门禁范围 `ruff check` / `ruff format --check`。验证：全部通过。**验证结果**：`ruff check apps/ config/ gateway/ shared/ models/ engines/` → All checks passed；改动文件 `ruff format --check` → 4 files already formatted；`manage.py check` 无问题。
- [x] 5.3 边界检查：`python tools/gen_arch_stats.py --check-boundaries`。验证：零违规。**验证结果**：`✅ 模块边界检查通过 — 零违规`。
- [x] 5.4 端到端实证（真实调用，属预期费用）：`python manage.py planner_eval --cases tests/ai_planner/cases/planner.yaml --repeat 1 --tag slim-digest`（模型用平台配置的 **deepseek-flash**）。验证：硬性 2/2；计划仍含明确入口名；如实记录费用。**并用只读探查复测摘要体积**：同一篇文档的全量 vs 瘦身后字符数，确认降幅（开工前实测 27473 → 12722）。**验证结果**：**硬性 2/2**（single-step 1 步 / multi-step 2 步）；报告 `tests/reports/planner_eval/slim-digest-20261008-125516.md`；**体积实测 27473 → 12722 字符（-54%）**，17 节点 / 16 连线 / 10 条路径全部保留、`elements` 与 `navigation_entries` 零残留、`parse_warnings` 为空；**计划仍命名入口**："在 APP主页找到「设备主页入口」并点击 → 页面跳转到设备主页页面，显示设备列表（可见 H6810 设备卡片）"。**费用同步下降**：单条 ¥0.0071 / ¥0.0068（改动前同口径约 ¥0.0134/条，**约减半**）。
- [x] 5.5 关单与归档：汇总改动清单、用例结果、体积降幅与费用；`openspec validate` 通过后归档（delta 并入 `ai-device-planner-tools`）。验证：`openspec validate "2026-10-08-slim-page-flow-digest"` 通过并完成归档。**验证结果**：改动清单 = `apps/workflow/semantics.py`（摘要瘦身 + 告警 + 删死代码）、`engines/ai/agents/config.py`（执行提示词三处）、两个用例文件（主收敛 + 扩展新增）、新增摘要用例、评测单测口径守卫、规格 delta；validate --strict 通过；已归档。
