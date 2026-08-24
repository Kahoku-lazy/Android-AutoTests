# PRD-11 — 评测中心 (Evaluator)

> 关联模块：`apps/evaluator/` · 前端：`frontend/src/modules/ai-assistant/EvaluatorTab.vue`（寄宿 ai-assistant 模块）
> 关联全局：`需求大纲.md`（评测中心暂无 §5.10，编号见 `文档编号对照表.md` §一）
> 关联上游：`PRD-08-AI助手.md`（前端寄宿与 §2.11 旧表述，见 §5 已知偏差登记）
> 版本：v1.0 · 状态：评审中 · 日期：2026-08-21

**修订记录**

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-08-21 | 初始契约：4 张 ev_ 表；legacy 14 路径 + DRF 3 ViewSet；LLM-as-Judge 四维评分 + 人工评分；4 套评测框架适配器；KB 自测；前端寄宿 ai-assistant |

---

## 1. 功能定位

评测中心是平台的 **AI 智能体质量评测工具**：以「题库（试卷）× 智能体」为评测单元，用独立的 Judge LLM（或外部评测框架）对智能体的答卷做四维打分（相关性 / 准确性 / 完整性 / 简洁性，1–5 分），支持人工评分纠偏，并提供知识库检索质量自测。其目的是让测试团队对 AI 智能体的回答质量形成可复现、可对比的量化评估。

**核心职责**：

| 模块 | 功能编号 | 核心职责 |
|------|----------|----------|
| ① 题库管理 | F-01-01 ~ F-01-04 | 试卷 CRUD（含嵌套题目）/ 默认 30 题试卷（幂等 seed） |
| ② 评测运行 | F-02-01 ~ F-02-03 | 选智能体 + 试卷 + 框架 → 后台线程评测 → 状态与进度 |
| ③ 结果与评分 | F-03-01 ~ F-03-03 | 逐题机器分 / 人工纠偏分 / 维度均值与总分 |
| ④ 评测框架 | F-04-01 ~ F-04-04 | self（LLM-as-Judge）与 evalscope / deepeval / maseval 适配器 |
| ⑤ KB 自测 | F-05-01 ~ F-05-02 | 知识库交互式检索测试 / 批量覆盖率自测 |

评测中心是 **管理模块（有写操作）**：题库、评测运行记录、人工评分均为本模块自有数据（`ev_` 前缀 4 张表），写操作落库；其数据来源（智能体、知识库）由 ai-assistant 模块（PRD-08）提供，本模块只读消费。

---

## 2. 功能详细规格

> 本章按五个功能模块分层，每模块依次说明：**功能实现逻辑 → 字段/规则表 → 组件 → 边界状态 → 验收标准**。
> 模块 ↔ 功能编号映射见 §1（F-xx-xx 用于 §5 API 交叉引用）。本章只写代码已实现的功能。

### 2.1 模块一：题库管理

**F-01-01 试卷列表**

**功能实现逻辑**：用户进入评测中心（或任一非 KB 子页）后，系统拉取全部试卷并展示（功能响应）。列表按 `updated_at` 倒序，每项含 id / name / description / question_count（题数，模型 property 实时统计）/ created_at。

**边界状态**：无试卷 → 列表为空，试卷管理条显示「已有 0 份试卷，共 0 题」。

**验收方式**：列表题数与后端一致；按 `updated_at` 倒序。

**F-01-02 试卷创建（含嵌套题目）**

**功能实现逻辑**：用户点击「新建试卷」→ 填写名称（必填）+ 描述（可选）+ 逐条添加题目（content / expected_keywords / category / order）→ 保存（用户动作）。系统校验名称非空后写库：先建试卷，再逐条建题目（功能响应）。

**字段/规则表**：

| 字段 | 必填 | 说明 |
|------|:--:|------|
| `name` | ✅ | 试卷名称，去空格后非空（空 → 400「试卷名称不能为空」） |
| `description` | — | 默认空串 |
| `questions[]` | — | 嵌套题目列表，可为空 |
| `questions[].content` | — | 题目文本，默认空串 |
| `questions[].expected_keywords` | — | 逗号分隔预期关键词，默认空串 |
| `questions[].category` | — | 类别，默认 `general` |
| `questions[].order` | — | 排序，缺省按数组下标 `i` |

**组件**：试卷编辑器弹窗 `EvaluatorTab.vue`（`showBankEditor` Dialog：名称 / 描述 / 题目列表，category 下拉固定 8 项：平台功能与架构 / 测试流程 / 设备管理 / 元素定位 / 知识库 / 异常处理 / 测试方法 / general）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| 名称为空 | 前端拦截「请输入试卷名称」，不发送请求 |
| 保存失败 | Toast「保存失败」 |
| 编辑试卷时题目加载失败 | Toast「题目加载失败，请勿直接保存以免清空题库」，不覆盖题目 |

**验收方式**：名称必填非空；题目列表随试卷一并创建；保存成功后列表刷新并 Toast「已保存」。

**F-01-03 试卷编辑（整题替换）**

**功能实现逻辑**：用户点「编辑试卷」→ 编辑名称 / 描述 / 题目列表 → 保存（用户动作）。系统更新 name / description；若提交了 `questions` 字段，则**先删除该试卷全部旧题，再按新列表重建**（功能响应，整题替换口径）。

**边界状态**：未提交 `questions` → 只更新名称 / 描述，题目不动；提交 `questions`（含空数组）→ 清空并重建。

**验收方式**：提交 questions 后题数 = 新列表长度；未提交 questions 时题目保持不变。

**F-01-04 默认 30 题试卷（幂等 seed）**

**功能实现逻辑**：用户点「创建默认30题试卷」（或后端调用 seed）（用户动作）。系统按名称「默认30题试卷」查重：已存在 → 幂等返回现有 id + `existed=true`（消息「默认试卷已存在，直接返回」）；不存在 → 创建试卷并批量写入内置 30 题（功能响应）。

**字段/规则表**：默认试卷名称「默认30题试卷」，描述「内置 30 道评测问题，覆盖平台功能、测试流程、设备管理、元素定位、知识库、异常处理、测试方法等 7 个类别」；题目来自 `default_questions.py` 的 `DEFAULT_QUESTIONS`（30 条，7 类别：平台功能与架构 6 / 测试流程 6 / 设备管理 4 / 元素定位 4 / 知识库 3 / 异常处理 4 / 测试方法 3）。

**边界状态**：默认试卷已存在 → 不重复建，返回原 id；前端在「已存在默认试卷」时禁用按钮（`banks.some(b=>b.name==='默认30题试卷')`）。

**验收方式**：首次 seed 后题数 = 30；再次 seed 幂等返回同一 id 且题数不变。

**F-01-05 试卷删除（级联）**

**功能实现逻辑**：系统按 bank_id 删除试卷，级联删除其下题目（功能响应）。前端当前版本**未提供删除试卷入口**（`evaluator-api.ts` 无 deleteBank；仅删除评测记录）。

**边界状态**：bank_id 不存在 → legacy 端点仍返回 `{status:true}`（静默幂等，无 404 校验）。

**验收方式**：删除后试卷及其题目消失；关联评测运行记录的 bank 置空（`on_delete=SET_NULL`）。

### 2.2 模块二：评测运行

**F-02-01 启动评测**

**功能实现逻辑**：用户选择智能体 + 试卷（self/自定义试卷模式必选）+ 裁判模型（默认 qwen-max）+ 框架 Tab → 点「开始评测」（用户动作）。系统校验 agent_id / bank_id 存在后创建 `EvalRun`（status=pending），并**在后台线程执行评测**，立即返回 run id 与提示「评测已开始，共 N 题」（功能响应）。

**字段/规则表（请求）**：

| 字段 | 必填 | 默认 | 说明 |
|------|:--:|------|------|
| `agent_id` | ✅ | — | 智能体 id（校验存在，否则 404「agent not found」） |
| `bank_id` | ✅ | — | 试卷 id（校验存在，否则 404「question bank not found」） |
| `framework` | — | `self` | `self` \| `evalscope` \| `deepeval` \| `maseval` |
| `judge_provider` | — | `dashscope` | 裁判模型供应商 |
| `judge_model` | — | `qwen-max` | 裁判模型 |

**边界状态**：

| 场景 | 行为 |
|------|------|
| 未选智能体 | 前端拦截「请选择智能体」，不发送请求 |
| 未选试卷（exam 模式） | 前端拦截「请选择试卷」 |
| agent_id 不存在 | 404「agent not found」 |
| bank_id 不存在 | 404「question bank not found」 |
| agent_id/bank_id 缺失 | 400「agent_id and bank_id are required」 |
| 启动中 | 「开始评测」按钮 loading 禁点 |

**验收方式**：合法请求立即返回 `{status:true, run:{id}, message}`；run 记录 status 由 pending → running → completed/failed。

**F-02-02 评测执行（后台线程）**

**功能实现逻辑**：系统在后台线程执行评测，分两条链路——`self` 走内置 LLM-as-Judge 引擎（`evaluator.run_evaluation`），外部框架走对应适配器（`get_adapter(framework).run`）。执行过程中逐题更新 `completed_questions` 进度；结束写 `status` / 各均值分 / `report_json` / `finished_at`（功能响应）。

**边界状态**：

| 场景 | 行为 |
|------|------|
| Agent 无 API Key | status=failed，report_json 记「Agent has no API key」 |
| Agent 或试卷缺失 | status=failed |
| 未知框架（adapter 为 None） | status=failed，report_json 记「Unknown framework: {framework}」 |
| 框架包未安装 | adapter 返回 `ok=false`，status=failed，error 提示 `pip install xxx` |
| 执行中异常 | status=failed，report_json 记异常信息 |

**验收方式**：`self` 逐题落库 ev_results 并推进 completed_questions；外部框架结束后写 report_json；异常时 status=failed 且 report_json 含 message。

**F-02-03 评测记录列表与轮询**

**功能实现逻辑**：系统拉取评测记录列表（按 `created_at` 倒序，**取最近 50 条**），按当前框架 Tab 过滤展示（`framework` 归一到 `self`）。启动评测后前端按 `EVALUATOR_POLL_MS`（2s）轮询 run 详情，直到 status 为 completed / failed 停止（功能响应）。

**字段/规则表（列表项）**：id / agent_id / agent_name（缺失显示 `?`）/ framework / bank_id / bank_name / status（pending\|running\|completed\|failed）/ total_questions / completed_questions / total_score / 四维均值 avg_relevance / avg_accuracy / avg_completeness / avg_conciseness / created_at / finished_at。

**边界状态**：无记录 → 空态「暂无评测记录」；status=running → 「详情」按钮禁用，展示 `completed_questions/total_questions` 进度；轮询到 completed 或 failed 停止并 Toast「评测完成」。

**验收方式**：列表按 created_at 倒序且 ≤50 条；Tab 过滤正确（framework 归一到 self）；轮询 2s 一次、到达终态停止。

### 2.3 模块三：结果与评分

**F-03-01 评测详情查看**

**功能实现逻辑**：用户点「详情」（running 禁用）（用户动作）。系统读取 run 详情：run 元信息 + 四维均值 + 总分 + 逐题结果（仅 self 框架含 results 数组；外部框架展示 report_json 原始输出）（功能响应）。

**字段/规则表（逐题结果项）**：id / question_id / question_text（截 200 字）/ agent_response（截 500 字）/ 机器四维分 relevance_score / accuracy_score / completeness_score / conciseness_score / 人工四维分 human_relevance / human_accuracy / human_completeness / human_conciseness / human_note / 生效四维分 effective_relevance / effective_accuracy / effective_completeness / effective_conciseness / judge_reasoning（截 300 字）。

**边界状态**：loading → 「加载中...」；外部框架（framework ≠ self）→ 展示 report_json 的「评测原始输出」（`prettyJson` 格式化），不展示逐题人工评分。

**验收方式**：详情含 run 元信息 + 均值分 + 总分；self 框架逐题展示机器分 / 人工分 / 裁判理由；外部框架展示原始输出。

**F-03-02 人工评分纠偏**

**功能实现逻辑**：用户在逐题结果区，对四维（相关 / 准确 / 完整 / 简洁）分别下拉选 1–5 分（可清空）调整人工分（用户动作）。系统写入对应 `human_*` 字段，并**重算所属 run 的四维均值与总分**（功能响应）。

**字段/规则表（生效口径）**：每题 `effective_*` = 人工分（若非空）否则机器分；run 均值 = 所有「任一维度 >0」的题目的 effective 均值（round 2 位）；`total_score` = 四维均值再取平均（round 2 位）。单题保存成功返回 `{result_id, scored:true}`。

**边界状态**：评分提交失败 → Toast「评分提交失败，请稍后重试」；提交后自动刷新详情。

**验收方式**：人工分落库后 effective 值切换为人工分；run 均值与总分随之重算；人工分清空后回退机器分。

**F-03-03 评测记录删除**

**功能实现逻辑**：用户点「删除」→ 二次确认（用户动作）。系统按 run_id 删除评测记录（级联删除其 ev_results）（功能响应）。

**边界状态**：取消确认 → 不删除；删除失败 → Toast「删除失败，请稍后重试」；删除成功 → Toast「已删除」并刷新列表。

**验收方式**：确认后记录及其结果消失；前端二次确认文案「确定要删除这条评测记录吗？」。

### 2.4 模块四：评测框架

**F-04-01 self（LLM-as-Judge，内置）**

**功能实现逻辑**：`self` 为内置评测引擎：逐题调智能体模型作答（max_tokens 2048，timeout 120s），再用**独立的 Judge LLM**（temperature 0.1，max_tokens 512，timeout 60s）按四维 1–5 分打分并解析 JSON 评分（功能响应）。详见 §4.1。

**F-04-02 evalscope / F-04-03 deepeval / F-04-04 maseval（外部框架适配器）**

**功能实现逻辑**：三者经统一 `BaseAdapter` 接口实现（`register(key)` 注册 + `is_available()` 探测 + `run(agent_config, questions)` → `AdapterResult`）。框架 Tab 通过 `/frameworks` 端点读取注册适配器的 name / description / available（是否已安装）；未安装 → Tab 显示「未安装」角标并禁用「开始评测」。执行时走适配器归一化结果，写入 run 的 report_json（不写 ev_results 表）（功能响应）。

**框架差异表**：

| 框架 key | 名称 | 探测包 | 评分口径 | 落库 |
|------|------|------|------|------|
| `self` | 答卷评分（内置） | 无需安装 | Judge LLM 四维 1–5 分 | ev_results + report_json |
| `evalscope` | EvalScope | `evalscope` | 临时 jsonl 自定义数据集 → run_task，归一化（total_score 恒 0，原始输出见 raw） | report_json |
| `deepeval` | DeepEval | `deepeval` | AnswerRelevancy（阈值 0.5）+ GEval completeness，指标分归一化 | report_json |
| `maseval` | MASEval | `maseval` | 关键词命中率（命中数/关键词数 ×5，1 位小数） | report_json |

**边界状态**：框架未安装 → Tab 显示「⚠️ XX 尚未安装，请联系管理员启用后使用」，按钮禁用；adapter 运行异常 → status=failed。

**验收方式**：`/frameworks` 返回 3 个外部框架的 available 状态；未安装 Tab 禁用；已安装框架启动后 run 落 report_json 且 status 为 completed/failed。

### 2.5 模块五：KB 自测

**F-05-01 交互式检索测试**

**功能实现逻辑**：用户在 KB 子页输入查询词 → 点「查询」（用户动作）。系统调 ai-assistant 的 `search_knowledge(query, top_k)` 检索知识库，返回命中文档（source / score / content 截 800 字）（功能响应）。

**字段/规则表（请求）**：`query`（必填非空，否则 400「query required」）、`top_k`（默认 5，前端 `KB_SEARCH_TOP_K`）。无效 JSON → 400「无效的 JSON」。

**边界状态**：query 为空 → 前端拦截「请输入查询内容」；检索异常 → 前端降级展示「搜索暂不可用，请稍后重试」；无命中 → 显示「无匹配结果」。

**验收方式**：返回 `{status, query, total, documents[]}`；top_k 默认 5；空查询 400。

**F-05-02 批量覆盖率自测**

**功能实现逻辑**：用户点「自动批量自测」（用户动作）。系统按**后端内置 8 条预定义查询**（`KB_TEST_QUERIES`）逐条 `search_knowledge(query, top_k=3)`，汇总覆盖率为「有结果的查询占比」（%，1 位小数）与「Top-1 平均相关度」（3 位小数），并返回逐查询明细（功能响应）。

**字段/规则表（响应）**：`score.coverage`（%）、`score.avg_relevance`、`score.total_queries`、`details[]`（每查询含 query / total_hits / top_score / documents[]）。

**边界状态**：无命中查询 → total_hits=0，不计入 top_scores。

**验收方式**：覆盖率 = 有结果查询数 / 总查询数 ×100%；返回逐查询明细与来源/分值。

---

## 3. 布局与视觉设计

> 颜色 / 字号引用 Doodle Craft 令牌（`frontend/CLAUDE.md` §2）；本页实际使用 ai-assistant 模块色令牌 `--ai-*` + 平台令牌 `--app-*`。字面量色值属例外，在 §9 C-09 登记。

### 3.1 页面布局（五区块）

```
┌───────────────────────────────────────────────────────┐
│ 子 Tab 栏：答卷评分 | 知识库评测 | EvalScope | DeepEval | MASEval │
├───────────────────────────────────────────────────────┤
│ ① 公共配置区（非 KB）                                   │
│   智能体下拉 + 试卷下拉 + 裁判模型输入（self）             │
│   / 框架专属：基准跑分·自定义试卷切换 + 基准卡 / 指标勾选   │
│   🚀 开始评测                                          │
├───────────────────────────────────────────────────────┤
│ ② 试卷管理条（非 KB）：+新建试卷 · 📋创建默认30题试卷 · 计数 │
├───────────────────────────────────────────────────────┤
│ ③ 评测记录列表（按框架 Tab 过滤）：状态标签 / 智能体 / 框架 / 试卷 / 总分 / 进度 │
├───────────────────────────────────────────────────────┤
│ ④ 评测详情（点击展开）：四维均值 + 总分 / 原始输出 / 逐题机器分·人工分 │
├───────────────────────────────────────────────────────┤
│ ⑤ KB 自测（KB Tab）：交互式检索 + 自动批量自测（覆盖率/相关度/查询数）│
└───────────────────────────────────────────────────────┘
```

- 页面底色：米白纸纹，卡片式 `doc-section`（`--app-bg-card` + `--app-radius-md` + 扁平阴影）。
- 子 Tab：胶囊按钮（`--ai-warm-border` 边框 / `--ai-warm-bg` 底），active 态青绿色 `--ai-teal`。
- 响应式：子 Tab 与配置表单 `flex-wrap: wrap` 换行。

### 3.2 颜色令牌与状态色

| 用途 | 令牌 |
|------|------|
| 卡片底 / 边框 | `--app-bg-card` / `--ai-bg-subtle` |
| 正文 / 标题 | `--ink` / 标题 `--app-font-display` |
| 辅助文本 | `--ai-ink-subtle` / `--ai-ink-soft` / `--ai-ink-muted` |
| 暖底面板（描述 / 结果卡片） | `--ai-warm-bg` + `--ai-warm-border` |
| Tab 激活 | `--ai-teal` / `--ai-teal-bg` / `--ai-teal-text` |
| 分数色（≥4 分） | `--c-workflow` |

**分数四档色（`scoreColor` 规则）**：`≥4` → `--c-workflow`（青绿）；`≥3` → `#f7cd67`（黄）；`≥2` → `#f7a8c4`（粉）；`<2` → `#e85f5f`（红）。状态标签：completed=success / running=warning / failed=danger / pending=info。

### 3.3 组件清单

| 区块 | 组件 | 说明 |
|------|------|------|
| 子 Tab | 内联按钮组 | 5 个框架 Tab，未安装显示「未安装」角标 |
| 公共配置 | Element Plus 表单（inline） | 智能体 / 试卷下拉、裁判模型输入、模式切换、基准卡、指标勾选 |
| 试卷编辑 | `el-dialog` 弹窗 | 名称 / 描述 / 题目列表（content + keywords + category + 删除） |
| 评测记录 | `run-card` 行 | 状态 / 智能体 / 框架 / 试卷 / 总分 / 进度 / 详情 / 删除 |
| 详情 | `score-badge` 徽章 | 综合总分 + 四维均值，逐题评分卡片 |
| KB 自测 | 检索输入 + 结果卡片 + 自测明细 | 覆盖率 / 平均相关度 / 测试查询数徽章 |

> 本页为单文件组件 `EvaluatorTab.vue`（未拆分子组件），样式 `scoped`。

---

## 4. 后端功能逻辑

> 产品口径，不写类成员清单与私有方法伪代码。

### 4.1 评分口径（self，LLM-as-Judge）

- **维度**：相关性（relevance）/ 准确性（accuracy）/ 完整性（completeness）/ 简洁性（conciseness），每维 1–5 分。
- **流程**：逐题调被测智能体模型作答 → 独立 Judge LLM（默认 `dashscope` / `qwen-max`，temperature 0.1，max_tokens 512）按固定评分提示词产出 JSON `{relevance, accuracy, completeness, conciseness, reasoning}` → 解析落库。
- **总分口径**：run 的 `total_score` = 四维均值（avg_relevance / avg_accuracy / avg_completeness / avg_conciseness）的算术平均，round 2 位；四维均值 = 已评分题目的各维均值（round 2 位）。
- **Judge 解析降级**：直接 `json.loads` → 剥离 ```` ```json ```` 围栏 → 取首个 `{...}` 块；全部失败则评分记 0、reasoning 记「Judge LLM 评分失败」。
- **鉴权降级**：Judge LLM 复用智能体 API Key（当前实现未单独配置裁判 Key）；智能体无 Key → 运行失败。

### 4.2 人工评分口径

- 每题 `effective_*` = 人工分（`human_*` 非空）优先，否则机器分。
- 提交人工分后，系统按「任一维度 >0 的题目」重算 run 四维均值与总分（口径同 §4.1）。
- 单维提交：请求体可只含部分字段（`{human_relevance: 5}`），其余维度不动。

### 4.3 外部框架口径

- 统一经 `BaseAdapter.run(agent_config, questions) → AdapterResult`（`ok / error / total_score / scores / items / raw`），执行于后台线程。
- 归一化后仅写 `EvalRun`：`total_score`、`total_questions`、`completed_questions`、`report_json`（含 framework / total_score / scores / items / raw / message）、`finished_at`；**不写 `ev_results` 表**。
- 框架差异见 §2.4 框架差异表；未安装探测失败 → 返回 error 提示 `pip install <包>`。

### 4.4 默认题库口径

- 默认试卷固定名称「默认30题试卷」，30 题、7 类别（平台功能与架构 6 / 测试流程 6 / 设备管理 4 / 元素定位 4 / 知识库 3 / 异常处理 4 / 测试方法 3），见 `default_questions.py`。
- seed 幂等：按名称查重，已存在直接返回。

### 4.5 状态机（EvalRun.status）

```
pending → running → completed | failed
```

- 创建即 `pending`；后台线程置 `running` 后逐题推进 `completed_questions`；结束置 `completed` / `failed`（附 `finished_at`）。
- 失败原因（无 Key / 未知框架 / 未安装包 / 异常）均写入 `report_json` 的 message 字段，不向上抛出。

### 4.6 写库收敛与现状

- legacy 写路径：views.py → `api.py`（`__all__` 白名单 7 个函数）→ ORM。
- 评测引擎运行时状态更新（`evaluator.run_evaluation` 及后台线程内的 run 状态写入）属 service 层内部编排，按 `api.py` 约定不收敛于 `api.py`。
- **现状偏差**：DRF 的 `QuestionBankSerializer.create/update` 直接 ORM 写 QuestionBank/Question，未走 `api.py`（见 §5 已知偏差登记）。

---

## 5. API 接口功能

鉴权：全部 HTTP 端点需 JWT Bearer。JSON 字段 snake_case。路由前缀 `/api/evaluator/`（`config/urls.py` 第 31 行 `path("api/evaluator/", include("apps.evaluator.urls"))`）。

**信封差异（按代码实际）**：

- **legacy 端点**：views.py 用 `JsonResponse` 直接返回**平铺信封** `{status: true/false, ...业务字段}`，**不套 `data`**（失败 `{status:false, message}`）。
- **DRF 端点**：经全局 `EnvelopeJSONRenderer`（`shared/renderers.py`，settings 默认渲染器）——成功（2xx）包装为 `{status: true, data: {...}}`；错误（4xx/5xx）包装为 `{status: false, message}`（保留 detail/字段错误取首条）。

### 5.1 端点总览

**Legacy（14 条，无尾斜杠）**

| # | 方法 | 端点 | 功能 | 前端消费 |
|---|------|------|------|:--:|
| 1 | GET | `/api/evaluator/banks` | 试卷列表（F-01-01） | ✅ listBanks |
| 2 | POST | `/api/evaluator/banks/create` | 创建试卷（F-01-02） | ✅ createBank |
| 3 | POST | `/api/evaluator/banks/seed` | 默认 30 题试卷（F-01-04） | ✅ seedDefaultBank |
| 4 | GET | `/api/evaluator/banks/{bank_id}` | 试卷详情（含题目）（F-01-01） | ✅ getBank |
| 5 | POST | `/api/evaluator/banks/{bank_id}/update` | 编辑试卷（F-01-03） | ✅ updateBank |
| 6 | POST | `/api/evaluator/banks/{bank_id}/delete` | 删除试卷（F-01-05） | ❌ |
| 7 | GET | `/api/evaluator/runs` | 评测记录列表（≤50）（F-02-03） | ✅ listRuns |
| 8 | POST | `/api/evaluator/runs/start` | 启动评测（F-02-01） | ✅ startRun |
| 9 | GET | `/api/evaluator/runs/{run_id}` | 评测详情（F-03-01） | ✅ getRun |
| 10 | POST | `/api/evaluator/runs/{run_id}/delete` | 删除评测记录（F-03-03） | ✅ deleteRun |
| 11 | POST | `/api/evaluator/results/{result_id}/score` | 人工评分（F-03-02） | ✅ submitScore |
| 12 | GET | `/api/evaluator/frameworks` | 框架可用性列表（F-04） | ✅ listFrameworks |
| 13 | POST | `/api/evaluator/kb-search` | 交互式检索测试（F-05-01） | ✅ kbSearch |
| 14 | POST | `/api/evaluator/kb-self-test` | 批量覆盖率自测（F-05-02） | ✅ kbSelfTest |

**DRF（17 条注册路由，带尾斜杠；前端当前均未消费）**

| # | 方法 | 端点 | 功能 | 可用 |
|---|------|------|------|:--:|
| 1 | GET | `/api/evaluator/banks/` | 试卷列表 | ✅ |
| 2 | POST | `/api/evaluator/banks/` | 创建试卷（嵌套题目） | ✅ |
| 3 | GET | `/api/evaluator/banks/{id}/` | 试卷详情 | ✅ |
| 4 | PUT | `/api/evaluator/banks/{id}/` | 全量更新 | ✅ |
| 5 | PATCH | `/api/evaluator/banks/{id}/` | 部分更新 | ✅ |
| 6 | DELETE | `/api/evaluator/banks/{id}/` | 删除 | ✅ |
| 7 | POST | `/api/evaluator/banks/seed/` | 默认 30 题试卷（@action） | ✅ |
| 8 | GET | `/api/evaluator/runs/` | 评测记录列表（摘要） | ✅ |
| 9 | POST | `/api/evaluator/runs/` | 创建记录（非推荐入口） | ✅ |
| 10 | GET | `/api/evaluator/runs/{id}/` | 评测详情（含 results） | ✅ |
| 11 | PUT | `/api/evaluator/runs/{id}/` | 全量更新 | ⛔ 405 |
| 12 | PATCH | `/api/evaluator/runs/{id}/` | 部分更新 | ⛔ 405 |
| 13 | DELETE | `/api/evaluator/runs/{id}/` | 删除 | ✅ |
| 14 | POST | `/api/evaluator/runs/start/` | 启动评测（@action） | ✅ |
| 15 | GET | `/api/evaluator/results/` | 结果列表 | ✅ |
| 16 | GET | `/api/evaluator/results/{id}/` | 结果详情 | ✅ |
| 17 | POST | `/api/evaluator/results/{id}/score/` | 人工评分（@action） | ✅ |

> DRF `runs` 的 update/partial_update 两条因 `http_method_names=["get","post","delete","head","options"]`（views_api.py）被关闭，返回 405；`POST /runs/`（create）路由存在但非推荐入口（评测统一走 `start`）。**前端消费全部走 legacy 13 条**（除 legacy #6 删除试卷外），DRF 端点当前无前端消费。

### 5.2 字段契约（代表性端点）

**legacy 试卷详情 `GET /banks/{bank_id}`**（平铺信封）：

`{status, bank:{id, name, description, questions:[{id, content, expected_keywords, category, order}]}}`

**legacy 评测详情 `GET /runs/{run_id}`**（平铺信封）：

`{status, run:{id, agent_id, agent_name, framework, bank_name, status, total_questions, completed_questions, total_score, avg_relevance/avg_accuracy/avg_completeness/avg_conciseness, report_json, created_at, finished_at, results:[...]}}`

**DRF 试卷序列化（QuestionBankSerializer）**：`id / name / description / questions[] / question_count / created_at / updated_at`（id、question_count、created_at、updated_at 只读；questions 嵌套 QuestionSerializer：id/content/expected_keywords/category/order）。

**DRF 运行序列化**：list 用 `EvalRunListSerializer`（不含 results）；retrieve 用 `EvalRunSerializer`（含 results，经 `_prefetched_results` 预取）。

**DRF 结果序列化（EvalResultSerializer）**：机器四维 + 人工四维 + `effective_*`（4 个）+ judge_reasoning（见 §2.3 字段表）。

**KB 自测 `POST /kb-self-test`**（平铺信封）：`{status, score:{coverage, avg_relevance, total_queries}, details:[{query, total_hits, top_score, documents:[{source, score, content_preview, content_length}]}]}`。

### 5.3 错误码汇总

| 状态码 | 场景 |
|:--:|------|
| 400 | 试卷名称空「试卷名称不能为空」/ agent_id+bank_id 缺失 / query 空 / 无效 JSON |
| 404 | agent 不存在 / 试卷不存在 / run 不存在 / result 不存在（均「not found」类） |
| 405 | DRF runs 的 PUT/PATCH（http_method_names 关闭） |
| 401/403 | 未认证 / 无权限（JWT 全局） |

### 5.4 契约变更

| 版本 | 变更 |
|------|------|
| v1.0 | 初始契约：legacy 14 路径（平铺信封）+ DRF 3 ViewSet（经 EnvelopeJSONRenderer `{status,data}`）；legacy/DRF 双路由并存；前端仅消费 legacy |

### 5.5 已知偏差登记

| 偏差 | 说明 |
|------|------|
| legacy / DRF 双路由并存未收敛 | 同一能力（题库 CRUD / 运行生命周期 / 人工评分）同时存在 legacy 平铺信封路径与 DRF `{status,data}` 信封路径；前端当前只消费 legacy 13 条，DRF 17 条注册路由无前端消费。属迁移期并存，未做唯一化收敛。 |
| DRF 序列化器直写 ORM（未收敛 api.py） | `QuestionBankSerializer.create/update` 直接 `Question.objects.create` / `bank.questions.all().delete()`，绕过 `api.py` 的 `create_question_bank` / `update_question_bank`，与「写库收敛 api.py」约定不一致（DRF 路径当前无前端消费，风险暂未暴露）。 |
| PRD-08 §2.11 两行旧表述与本 PRD 的关系 | PRD-08 §2.11 描述「评测中心 Tab 提供自然语言用例生成与执行：输入自然语言 → 选设备 → 生成用例或直接执行」，与实际代码不符——实际为「题库 × 智能体的四维评分评测 + KB 自测」，不涉及用例生成/设备执行。本 PRD 为评测中心的准确规格，PRD-08 §2.11 视为待修正的旧表述（用例生成/执行属 PRD-08 其他能力，非评测中心）。 |
| KB 自测查询数文案偏差 | 前端文案「使用 10 个预定义查询」，后端 `views.py` 的 `KB_TEST_QUERIES` 实际为 **8 条**（响应 `total_queries=8`）；管理命令 `kb_self_test.py` 另有一份 10 条列表。文案与线上端点口径不一致，属待修正项。 |

---

## 6. 数据来源表

| 表 | 表前缀 | 职责 |
|------|:--:|------|
| `ev_question_banks` | ev_ | **本模块自有表**：试卷（名称 / 描述 / 时间戳），`question_count` 为 property 非字段 |
| `ev_questions` | ev_ | **本模块自有表**：题目（外键试卷 / 内容 / 预期关键词 / 类别 / 排序） |
| `ev_runs` | ev_ | **本模块自有表**：评测运行记录（智能体 × 试卷 / 状态 / 框架 / 裁判配置 / 四维均值 / 总分 / report_json） |
| `ev_results` | ev_ | **本模块自有表**：逐题结果（机器四维 + 人工四维 + 裁判理由） |

> 跨模块只读消费（不属本模块）：`ai_agents`（智能体，经 ai-assistant，主权 PRD-08）；知识库检索经 ai-assistant `search_knowledge`（ChromaDB，主权 PRD-08）。

**字段数（按 models.py 计，不含 property）**：`ev_question_banks` 4 · `ev_questions` 6 · `ev_runs` 16 · `ev_results` 15，合计 **41**。

---

## 7. 非功能需求

| 类别 | 指标 | 目标值 |
|------|------|------|
| 容量 | 默认题库题数 | 30 题（7 类别：6/6/4/4/3/4/3） |
| 容量 | 评测记录列表 | 最近 50 条（`[:50]`，无 offset/limit 分页） |
| 性能 | 评测进度轮询 | 2s（`EVALUATOR_POLL_MS = 2000`） |
| 性能 | Judge LLM 调用 | temperature 0.1 / max_tokens 512 / timeout 60s |
| 性能 | 智能体作答 | max_tokens 2048 / timeout 120s |
| 可靠性 | 后台线程执行 | 评测在 daemon 线程异步执行，接口即时返回不阻塞 |
| 可靠性 | 失败降级 | 失败写入 status=failed + report_json.message，不外抛 |
| 容量 | KB 交互检索 top_k | 默认 5（`KB_SEARCH_TOP_K`）；批量自测固定 top_k=3 |
| 可靠性 | 默认试卷 seed | 幂等（按名称查重） |
| 安全 | 鉴权 | 全部端点 JWT Bearer；API Key 解密后仅用于模型调用，不落日志 |
| 兼容性 | 框架可探测 | 3 个外部框架按包安装状态返回 available，未安装禁用 |

---

## 8. 非目标（Non-goals）

| 不做的功能 | 原因 |
|-----------|------|
| AI 对话 / SSE 流式对话 | 属 ai-assistant（PRD-08）唯一 SSE 通道；评测中心只做异步批量评测 |
| 自然语言生成用例 / 用例执行 | 属 PRD-08 / case-manager（PRD-05）/ test-runner（PRD-06）；PRD-08 §2.11 旧表述待修正 |
| 知识库主权（文档导入 / 索引 / 管理） | 知识库归 ai-assistant（PRD-08）；本模块只读检索做自测 |
| 设备操控 / 元素定位 | 属 device-pool / element-locator（PRD-02/04） |
| 评测报告导出 / 趋势图 / 邮件推送 | 未实现；外部框架原始输出仅以 report_json 文本展示 |
| 裁判模型独立密钥配置 | 当前 Judge LLM 复用智能体 API Key（代码注释已标注可扩展） |
| 评测任务队列 / 并发上限 / 重试 | 当前无任务队列与重试，仅 daemon 线程串行执行 |

---

## 9. 关键约束速查

| 编号 | 约束 | 实施位置 |
|------|------|------|
| C-01 | 自有表 `ev_*` 前缀（`ev_question_banks/ev_questions/ev_runs/ev_results`），`db_table` 显式指定 | `apps/evaluator/models.py` |
| C-02 | 写库收敛 `api.py`（`__all__` 白名单 7 函数）；评测引擎运行时状态更新属 service 内部编排例外 | `apps/evaluator/api.py` |
| C-03 | 跨模块读 Model ✅（`ai_assistant.AIAgent`）；跨模块检索走 `ai_assistant.api.search_knowledge` / `decrypt_key` / `get_provider_config` | `views.py` / `views_api.py` / `evaluator.py` |
| C-04 | 信封差异：legacy 平铺 `{status,...}`；DRF 经 `EnvelopeJSONRenderer` `{status,data}` / 错误 `{status,message}` | `views.py` vs `views_api.py` + `shared/renderers.py` |
| C-05 | 前端寄宿边界：评测 UI 在 `EvaluatorTab.vue`，API 经 `evaluator-api.ts`（`/evaluator/*`），不另起 HTTP 客户端 | `frontend/src/modules/ai-assistant/` |
| C-06 | 路由前缀 `/api/evaluator/`；legacy 无尾斜杠、DRF 带尾斜杠 | `config/urls.py` + `apps/evaluator/urls.py` |
| C-07 | 评分 1–5 分制，总分 = 四维均值再平均（round 2 位）；effective = 人工分优先覆盖机器分 | `evaluator.py` / `api.py` |
| C-08 | 评测异步：daemon 线程执行，接口即时返回；前端 2s 轮询至终态 | `views.py` / `views_api.py` / `constants.ts` |
| C-09 | 颜色/字号走 Doodle Craft 令牌；分数四档色 `#f7cd67/#f7a8c4/#e85f5f` 与 Tab 紫 `#b39ef3/#f3f0ff/#5b4aa8`、暖文本 `#8a7b66`、未安装提示 `#fff3e0/#e65100` 为字面量例外 | `EvaluatorTab.vue` |
| C-10 | 智能体 / 知识库数据主权归 ai-assistant（PRD-08），本模块只读消费 | §6 数据来源表 |

---

## 10. 相关文件索引

| 层 | 文件 | 说明 |
|----|------|------|
| 前端 | `frontend/src/modules/ai-assistant/EvaluatorTab.vue` | 评测中心页面（寄宿 ai-assistant，单文件组件） |
| 前端 | `frontend/src/modules/ai-assistant/evaluator-api.ts` | 评测 13 条 legacy 端点 + ai-assistant agents 列表封装 |
| 前端 | `frontend/src/modules/ai-assistant/constants.ts` | `EVALUATOR_POLL_MS=2000` / `KB_SEARCH_TOP_K=5` |
| 后端 | `apps/evaluator/models.py` | 4 张 ev_ 表定义 |
| 后端 | `apps/evaluator/urls.py` | DRF router（banks/runs/results）+ legacy 14 路径 |
| 后端 | `apps/evaluator/views.py` | legacy 视图（14 端点，薄层，调 api.py） |
| 后端 | `apps/evaluator/views_api.py` | DRF 3 ViewSet + @action（seed/start/score） |
| 后端 | `apps/evaluator/api.py` | 写操作白名单（7 函数） |
| 后端 | `apps/evaluator/serializers.py` | DRF 序列化器（QuestionBank/Question/EvalRun/EvalResult） |
| 后端 | `apps/evaluator/evaluator.py` | LLM-as-Judge 引擎（作答 + 裁判 + 评分落库） |
| 后端 | `apps/evaluator/default_questions.py` | 默认 30 题题库（7 类别） |
| 后端 | `apps/evaluator/frameworks/` | base + evalscope/deepeval/maseval 适配器 |
| 后端 | `apps/evaluator/management/commands/kb_self_test.py` | KB 自测管理命令（10 查询，独立于 HTTP 端点） |
| 路由 | `config/urls.py` | `api/evaluator/` 挂载（第 31 行） |

---

## 附录A：功能边界规则

| 边界 | 规则 |
|------|------|
| 我能做什么 | 试卷 CRUD（含嵌套题目）+ 默认 30 题试卷 seed；选智能体 × 试卷启动评测（self / evalscope / deepeval / maseval）；查看评测详情与逐题机器分；提交人工评分纠偏并重算均值/总分；删除评测记录；知识库交互检索与批量覆盖率自测 |
| 我不能做什么 | AI 对话 / SSE 流式；自然语言生成用例与用例执行；知识库文档导入/索引/管理；设备操控/元素定位；评测报告导出/趋势图/邮件推送 |
| 如需越界 | 智能体与知识库经 ai-assistant（PRD-08）；用例执行经 case-manager / test-runner（PRD-05/06）；设备经 device-pool（PRD-02） |
| 数据可见性 | ev_ 数据为本模块自有表；评测记录关联智能体（`ai_agents`）与试卷（`ev_question_banks`），当前无按用户隔离；智能体/知识库可见性见 PRD-08 |
