## 1. 后端：对照表读取与只读端点

- [x] 1.1 新增 `apps/ai_assistant/log_keywords.py`：`collect_keywords()` 按「运行中总线索引 → 直读配置文件」取值，返回 `{keywords: [{keyword, features:[{id,module,feature}]}], keyword_count, feature_count, origin: "runtime"|"file"|"none", keyword_file, updated_at, note}`；关键词保持**表内顺序**，不含任何写操作。验证：新增 `tests/graybox/unit/test_ai_log_keywords.py` 覆盖「有总线取运行索引」「无总线读文件」「文件缺失 / 不可解析给空列表与可读 note」，且断言不写入任何模型。验证结果：7 项通过；功能点计数按「模块 + 编号 + 名称」去重（4 个关键词含 5 个不同功能点的桩表断言为 5）；缺失 / 损坏 / 未配置三种情形都返回 `origin=none` 与可读 note。
- [x] 1.2 新增 `apps/ai_assistant/views_log_keywords_drf.py`（`GET /api/ai/log-keywords/`，登录可读、信封 `{status,data}`）+ `urls.py` 注册路由。验证：端点用例断言未登录 401、登录 200 且 `data.keywords` 非空、`data.keyword_count` 与表一致；`python -m pytest tests/graybox/unit/test_ai_log_keywords.py -q` 全绿。验证结果：端点用例通过（普通登录用户即可读、响应信封 `status=true`）；重启后端后对运行中的服务实测：未登录 `HTTP 401 {"status":false,"message":"请先登录"}`，超管实测返回 `keyword_count=67 / feature_count=56 / origin=runtime`，与磁盘表一致。

## 2. 前端：来源入口与目录面板

- [x] 2.1 `helpers/toolbox-assembly.ts`：`AssemblySourceKey` 增 `"keywords"`，`ASSEMBLY_SOURCES` 增来源 `{key:"keywords", name:"日志关键词", desc:"关键词 → 功能模块 / 功能点（只读）", gateKey:"", meta:"关键词 → 功能模块 / 功能点 · 只读"}`。验证：既有 `npx vitest run tests/ai-assistant/p0/toolbox-assembly-port-source.spec.ts`（含「无总闸来源副标题一律不含计数」公共断言）仍全绿。验证结果：该公共断言自动覆盖新来源并通过；另新增装配台入口用例断言「来源行在列表中、无总闸开关、不进未装配提示、选中后渲染关键词表格面板」。
- [x] 2.2 新增 `helpers/log-keyword-rows.ts`（纯函数）：把关键词对照拍成表格行（一行一个「关键词 × 功能点」，行标识 = 关键词|模块|编号|名称），行序**与表内逐行一致**（不重排、不合并）；`filterKeywordRows()` 以忽略大小写的包含匹配作用于关键词 / 模块 / 功能点；`keywordRowCounts()` 给全量计数（关键词去重、功能点按「模块 + 编号 + 名称」去重）。验证：新增 `frontend/tests/ai-assistant/p0/log-keyword-rows.spec.ts` 锁定行序、1:N 拆行、唯一行标识、缺名占位、计数去重与五条搜索口径。验证结果：10 项通过。
- [x] 2.3 新增 `composables/useLogKeywords.ts`（取数 + 载入/错误态）与 `api/toolbox.ts` 的 `fetchLogKeywords()`。验证：`npx vue-tsc --noEmit` 通过。验证结果：类型检查无输出、退出码 0；行与计数由纯函数派生，计数恒报全量（搜索时不缩水）。
- [x] 2.4 新增 `components/LogKeywordPanel.vue` + `LogKeywordPanel.style.css`：复用装配台页头 / 空错态范式与共享 `AppTable`；表格恰为三列（关键词 / 功能模块 / 功能点），上方搜索框 + `关键词数 · 功能点数 · 行数` + 取值来源与更新时间说明 + 「改表后需重启平台才用于判定」的如实标注；除搜索与页头「刷新」外无任何控件。`ToolboxPanel.vue` 在 `activeSource === "keywords"` 时渲染该面板。验证：新增 `frontend/tests/ai-assistant/p0/LogKeywordPanel.spec.ts` 覆盖「三列固定与行渲染」「计数」「搜索过滤 / 计数不缩水 / 清空回全量」「空表可读空态且不渲染表格」「只读」。验证结果：6 项通过；只读断言为「表格正文 0 个 button、唯一 input 是搜索框、无 file input、文案不含保存/删除，页头唯一操作是刷新」。

## 3. 收口

- [x] 3.1 后端关单：`python manage.py check`、`python manage.py makemigrations --check`、`python -m ruff check apps/ai_assistant`（相关路径）、`python -m pytest tests/graybox/unit/test_ai_log_keywords.py -q`。验证：全部通过。验证结果：`manage.py check` 无问题、`No changes detected`、`ruff check` + `ruff format --check` 通过；相关后端用例 23 项通过（关键词目录 7 + 无线端口 16，后者为同族回归）。
- [x] 3.2 前端关单：改动文件 `npx prettier --check`、`npx eslint src/modules/ai-assistant` 无新增 error、`npx vue-tsc --noEmit` 通过；`npx vitest run tests/ai-assistant/p0` 相关用例全绿。验证结果：prettier 全通过；eslint 10 warning / 0 error（全为存量）；`vue-tsc` 退出码 0；`tests/ai-assistant/p0` 全量 25 个文件 175 项通过（含本变更新增 18 项）。
- [x] 3.3 文档同步：AI 助手接口文档补 `GET /api/ai/log-keywords/`；`frontend/src/modules/ai-assistant/AGENTS.md` 的工具来源清单补「日志关键词」（现文档仍写「左三源」，一并校正）。验证：文档内新端点与字段与实现一致，来源清单与 `ASSEMBLY_SOURCES` 一致。验证结果：接口文档新增 8.2i 小节（取值优先级、字段表、空态口径）与速查表一行；模块文档改为「左六源」并写明「无总闸来源必须带 `meta`」的规则与新增面板的只读口径。
- [ ] 3.4 页面验收（用户侧）：AI 工具箱左侧出现「日志关键词」，点开后以**表格**展示（列为 关键词 / 功能模块 / 功能点，现场 67 个关键词 / 56 个功能点、约 70 行），搜索「switch」能筛出开关相关行，计数不缩水；除搜索与刷新外没有别的入口。验证：用户目视确认。
- [x] 3.5 呈现形式调整（需求方追加：改为表格）：`helpers/log-keyword-groups.ts` 及其用例改名为 `log-keyword-rows.ts` + `log-keyword-rows.spec.ts`（倒排分组 → 表格行拍平，行序改为与表内逐行一致），面板改用共享 `AppTable` 三列表格，规格 / 设计 / 任务单同步改写。验证：`npx vitest run tests/ai-assistant/p0/log-keyword-rows.spec.ts tests/ai-assistant/p0/LogKeywordPanel.spec.ts tests/ai-assistant/p0/ToolboxPanel-keyword-source.spec.ts` 全绿。验证结果：18 项通过；`openspec validate` 该变更仍为 valid。

