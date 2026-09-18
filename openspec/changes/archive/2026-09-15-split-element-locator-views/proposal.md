## Why

🔴 **`apps/element_locator/views.py` 1357 行**（`django-backend-check` calibration §4：`views*.py` 上限 300 行，**超 2×（600）即 🔴「只允许拆分」**；本文件为 **4.5×**）。它同时是 D3 写库收敛的前置阻塞 —— 其隐式写路径与 `api.py` 写函数返回 ORM 的纠缠需要先拆开才能收敛。

现状盘点（文件自带 8 个 `# ──` 分段，实测）：

| 段 | 行范围 | 内容 |
|---|---|---|
| — | 28-41 | `_optional_directory_id`（跨域 helper，被 web 元素与 api 端点两处使用） |
| Page CRUD | 44-545 | 页面 CRUD + 页面元素 CRUD（**单段 500 行**，需再分两片） |
| Flow CRUD | 546-592 | Android 页面流 |
| Web Element CRUD | 593-822 | Web 元素（含 `LOCATOR_TYPE_CHOICES` 常量） |
| Web Group CRUD | 823-953 | Web 分组 |
| Web Page Flow CRUD | 954-1041 | Web 页面流 |
| API Group CRUD | 1042-1172 | API 分组 |
| API Endpoint CRUD | 1173-1322 | API 端点 |
| 快照导入 | 1323-1357 | `import_snapshot` |

**消费方只有一个**：`apps/element_locator/urls.py`（导入 26 个符号）。无其他 App import 本文件（实测），故无兼容层包袱。

## What Changes

按文件**自带的段边界**拆分（不发明新分类），每片都落在 §4 的 300 行以内：

| 新模块 | 行数 | 内容 |
|---|---:|---|
| `views_pages.py` | 203 | 页面 CRUD（`_page_payload` / `list_pages` / `page_detail` / `create_page` / `pages_batch_move`） |
| `views_page_elements.py` | 297 | 页面元素（`_element_payload` / `add_element_to_page` / `batch_add_elements` / `clear_pages` / `page_elements` / `update_element`） |
| `views_flows.py` | 135 | Android 页面流 + Web 页面流（两个 flow 段合并） |
| `views_web.py` | 230 | Web 元素（含 `LOCATOR_TYPE_CHOICES`） |
| `views_web_groups.py` | 131 | Web 分组 |
| `views_api_assets.py` | 281 | API 分组 + API 端点 |
| `views_snapshot.py` | 35 | `import_snapshot` |

- **跨域 helper 归位**：`_optional_directory_id` 被 `views_web` 与 `views_api_assets` 两片共用（不能留在任一视图片里）→ 迁到目录域的 API 模块 `api_directories.py`，改名 `optional_directory_id`（公有）并登记 `__all__`；它做的事情就是「校验 directory_id 属于该 project」，属目录域职责
- **删除 `views.py`**：唯一消费方 `urls.py` 改为从 7 个新模块导入（无转发壳 —— 单一消费方不值得留一层间接）
- `tools/gen_arch_stats.py`：`has_views` 判据从 `views.py` 放宽为 `views*.py`（否则拆分后 element_locator 会在生成的报告里退化成 ❌「无视图」）；顺带修正 2 个**本就该是 ✅** 的 App（`ai_assistant` / `case_manager` 只有 `views_*.py`）
- **文档/注释同步**：`API-元素定位.md` 3 处「真相源：`views.py`」改为指向新模块 · `views_drf.py` 顶部 docstring 的「remain as plain Django views in views.py」改为新模块名
- 新增 `tests/graybox/unit/test_element_locator_views_split.py`：① 全部 legacy + router 路径仍 `resolve()` 到预期函数；② `element_locator` 下每个 `views*.py` 行数 ≤ 300（把 §4 阶梯钉成门禁，防回涨）

- **BREAKING**：无。**零行为变化** —— 函数体逐字搬迁、路由路径与名称不变、信封口径不变（legacy 平铺 / DRF 标准）
- 按 schema 约定设 `skip_specs: true`（拆分不改可观察契约）

## 关联文档

- 门禁：`django-backend-check/references/calibration.md` §4 文件行数阶梯（`views*.py` 300 / 1.5× / 2×）· §7
- App 约束：`apps/element_locator/AGENTS.md`（`urls.py` 为路径真相源；`page_tree.py` / `api_snapshot.py` 禁被其他 App import）· `apps/AGENTS.md` §1.2
- 契约真相源：`dev_docs/05-开发与测试/接口文档/API-元素定位.md`
- 前置分析：本会话 D3 复查（`views.py` 1357 行为 🔴 体积项，且阻塞写库收敛）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 不改 Requirement 文本，故无 delta）

## Impact

- 新增：`views_pages.py` · `views_page_elements.py` · `views_flows.py` · `views_web.py` · `views_web_groups.py` · `views_api_assets.py` · `views_snapshot.py`
- 删除：`views.py`
- 改动：`urls.py`（导入来源）· `api_directories.py`（+1 公有函数 +1 `__all__`）· `tools/gen_arch_stats.py`（`has_views` 1 行）· `views_drf.py`（docstring）
- 文档：`dev_docs/05-开发与测试/接口文档/API-元素定位.md`（3 处真相源指向）
- 测试：新增 `tests/graybox/unit/test_element_locator_views_split.py`
- 验证：`manage.py check`（加载 URLconf 即验证导入完整）· `makemigrations --check` · `ruff check .` / `format --check .` · 全量 `unit + arch + integration` · `--check-boundaries`
- **不在本单范围**：写库收敛（`views_*_drf.py` 的 `serializer.save()` 与 `api.py` 返回 ORM）—— 本单只拆文件、不动写路径；拆完即可另单收敛
