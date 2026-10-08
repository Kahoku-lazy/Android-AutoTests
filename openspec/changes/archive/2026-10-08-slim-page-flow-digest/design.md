# 设计：页面流摘要只给页面与节点关系（+ 执行提示词收口 + 评测口径收敛）

## Context

- **摘要构造点**：`apps/workflow/semantics.py::build_graph_digest`（`config` 的 nodes/links → dict）。当前每个页面/弹窗节点会带 `elements`（74 条，xpath 全空）与 `navigation_entries`（18 条）。
- **消费方实测**：`build_graph_digest` 经 `apps/workflow/api_digest.get_document_digest` 暴露，**全仓唯一消费者**是 AI 工具 `apps/ai_assistant/tools.py::get_page_flow`（规划模型）；`get_document_digest` / `build_graph_digest` 在 `tests/` 下**零引用**（该摘要此前没有测试覆盖）。
- **可命名的关键信息在连线上**：`links[].from_port_name` 实测非空（如「设备主页入口」），另有 `paths` 文本；故去掉元素清单不影响"写出明确点击目标"。
- **告警现状**：`parse_warnings` 的 4 个产生点中，「连线端口槽位不可解析」目前只由 `_collect_elements → _resolve_port_targets` 触发（页面节点专属）。去掉元素收集会让**页面节点**的这类告警消失——属诊断能力的退化，必须补回。
- **执行提示词现状**：`VISION_PROMPT` 有三处引用页面流（"优先使用页面流里的元素 xpath"×2、"按页面流的跳转边逐页推进"×1），但 `VISION_TOOLS` 里**没有页面流工具**，执行模型读不到页面流；摘要里的 xpath 也全为空。同文件 SOP 段自己的措辞是对的（"若步骤已给出元素 xpath，直接用 xpath 定位"）。
- **评测现状**：用例集 7 条（`tests/ai_planner/cases/planner.yaml`），上次实跑用了 flash 与 pro 两档。用户指定正式口径：**只用 deepseek-flash、只跑单步与多步**。

## Goals / Non-Goals

**Goals:**

- 规划读到的摘要只含页面与节点关系，体积/费用显著下降，且**仍能支撑命名点击目标**。
- 诊断（`parse_warnings`）不因瘦身而退化。
- 执行提示词不再声称它读不到的东西（三处空指令收口）。
- 评测口径收敛为「flash + 单步/多步」，其余用例保留为扩展资产。

**Non-Goals:**

- 不改页面流画布 / 前端 / HTTP 接口（该摘要不经 HTTP 下发）。
- 不改元素定位域：元素的真相源是元素定位域，不因本单改变；本单只是**不再从页面流摘要里给元素**。
- 不改连线、路径、起点字段的既有口径（`page-flow-start-node` 的要求原文不动，摘要仍只给 `start_kind`/`package_name`）。
- 不改工具名、参数与规划提示词的"先列后读"指引（规格原文保留）。
- 不为"将来给执行模型用页面流 xpath"预留数据位——需要时另立一单，从元素定位域取。

## Decisions

**D1 在摘要侧直接去掉元素清单（用户已选 A），不新增工具、不加参数。**

方案 B（新增"关系视图"工具）与 C（工具加 `detail` 参数）都要维护两份形状或让模型挑粒度，而"全量摘要"当前**没有任何别的消费方**——保留它没有收益。A 的改动面最小：一个函数内的一段构造 + 两处随之死掉的辅助。

**D2 告警补回连线遍历处，并去重。**

原来的"端口槽位不可解析"由元素收集顺带产生。改为在连线遍历（解析 `origin_slot`/`target_slot` 处）产生，且入 `warnings` 前查重，避免与弹窗路径（`_popup_close_targets → _resolve_port_targets`）重复记录同一连线。取舍：宁可多几行，也不让瘦身换来"诊断沉默"。

**D3 删掉随之变成死代码的 `_collect_elements` 与 `_element_source`。**

两者在本单后无任何引用（`_element_source` 只被 `_collect_elements` 使用）。`_resolve_port_targets` **保留**——弹窗的 `close_returns_to` 仍用它。关单前以 grep 复核"零引用"再删，避免留下误导性死函数。

**D4 执行提示词只改"与能力不符"的表述，不动 SOP 与工具用法。**

三处改为：视觉定位优先；元素 xpath **仅在步骤里明确给出时**使用（与同文件 SOP 的既有措辞一致）；推进**按步骤**而非"按页面流跳转边"。工具清单、截图铁律、`xpath_action` 的用法一律不动——`xpath_action` 仍可用（步骤给 xpath 或人给 xpath 的场景）。

**D5 评测口径 = flash + 单步/多步；扩展用例单独成文件。**

主用例集 `tests/ai_planner/cases/planner.yaml` 只留 `single-step` 与 `multi-step`；其余 5 条移入 `tests/ai_planner/cases/extended.yaml`（同格式，可按需 `--cases` 指定）。命令不变（`--cases` 必填），故"默认口径"由**文件内容 + 文档**表达，而不是写死模型名——`--model` 仍是能力，只是我们的验证只用 flash。

**D6 摘要形状要靠测试钉住（此前零覆盖）。**

新增用例以合成 config 直接构建摘要，断言：① 节点无 `elements`/`navigation_entries`；② 连线保留 `from_port_name`；③ `paths` 仍产出；④ 起点节点仍只输出 `start_kind`/`package_name`（守住既有规格）；⑤ 构造一条槽位不可解析的连线，断言 `parse_warnings` 仍记录。这样"元素悄悄塞回来"会在门禁处被拦住。

## 模块防火墙自检

- 跨 App import：无新增（改动在 `apps/workflow` 内部与引擎提示词常量）。
- 写库路径：零写库；无迁移（摘要为运行时构造，不落库）。
- 前端：零改动（该摘要不经 HTTP 下发）。
- 引擎边界：只改提示词常量文本，不新增依赖。
- 测试隔离：新增用例为纯函数级（合成 config，无数据库、无模型调用）。

## Risks / Trade-offs

- [将来要用页面流元素 xpath] → 本单明确：元素真相源在元素定位域；需要时另立一单从那里取，MUST NOT 从摘要塞回（D6 的测试会拦住偷偷塞回）。
- [瘦身导致规划变模糊] → 连线保留触发口名称 + 路径 + 出入关系；关单以 flash 跑单步/多步两条用例实证计划仍含明确入口名。
- [告警丢失] → D2 补回并去重；D6 用例覆盖。
- [删死代码误伤] → D3：删前 grep 复核零引用；`_resolve_port_targets` 保留。
- [评测口径写死在文件里被误改] → 评测单测补一条"主用例集恰为 2 条且为单步/多步"的守卫；扩展文件独立，误跑全量只是显式指定。
- [既有任务/页面对摘要的依赖] → 唯一消费方是 AI 工具且不落库；存量任务记录里存的是**计划**（plans），不是摘要，故不受影响。

## Migration Plan

1. `semantics.py`：去元素/入口清单 → 补告警 → 删死代码。
2. `config.py`：`VISION_PROMPT` 三处表述。
3. 用例集：主文件收敛为 2 条 + 新增 `extended.yaml`。
4. 测试：新增摘要形状用例 + 评测口径守卫。
5. 规格 delta（ADDED 一条需求）。
6. 验证：摘要新用例、评测单测、工作流/引擎相关用例、`manage.py check`、ruff、边界检查；**实跑** `planner_eval --model 默认（flash）` 只跑主用例集（2 条）→ 期望 2/2，并对比摘要体积下降。
7. 回滚：纯代码/文本改动，`git revert` 单次提交即可（无数据变更）。
