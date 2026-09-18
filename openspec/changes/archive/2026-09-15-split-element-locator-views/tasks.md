## 1. 复核（已完成）

- [x] 1.1 实测体量：拆分前 `views.py` **1357 行** → §4 上限 300 的 **4.5×**（🔴「只允许拆分」）
- [x] 1.2 清点结构：文件自带 8 个 `# ──` 分段；Page CRUD 单段 ~500 行需再分
- [x] 1.3 实测消费方：全仓仅 `urls.py`（25 个符号）；`views_drf.py:4` 仅 docstring 提及
- [x] 1.4 实测跨片耦合：`_optional_directory_id` 被 2 处使用（web 元素创建 · api 端点创建）→ 迁 `api_directories.optional_directory_id`；`LOCATOR_TYPE_CHOICES` 仅 Web 元素段内用
- [x] 1.5 确认 `gen_arch_stats.has_views` 只喂生成报告（:638/:878 的 ✅/❌），不影响 `--check-boundaries`
- [x] 1.6 实测装饰器分布（23 处 `@csrf_exempt`）并建立逐函数对照表 —— 用于校验搬家后装饰器无错配

## 2. 修改

- [x] 2.1 `views_pages.py`（236）· `views_page_elements.py`（196）· `views_page_element_batch.py`（120）
- [x] 2.2 `views_flows.py`（146）· `views_web.py`（240）· `views_web_groups.py`（141）
- [x] 2.3 `views_api_assets.py`（291）· `views_snapshot.py`（49）
- [x] 2.4 `api_directories.py`：加公有 `optional_directory_id` + `__all__`；`views_web` / `views_api_assets` 改从这里 import
- [x] 2.5 `urls.py` 改从 8 个新模块导入；**删除 `views.py`**（无转发壳）
- [x] 2.6 `tools/gen_arch_stats.py`：`has_views` 放宽为 `views*.py`（附理由注释）
- [x] 2.7 文档同步：`API-元素定位.md` 3 处真相源 · `views_drf.py` docstring
- [x] 2.8 新增 `tests/graybox/unit/test_element_locator_views_split.py`（41 条：31 legacy 路由 + 8 router + 行数上限 + `views.py` 已删）

## 3. 验证

- [x] 3.1 `python manage.py check` → **0 issues**（加载 URLconf 即证明 25 个导入全部解析）；`makemigrations --check` → `No changes detected`
- [x] 3.2 `python -m ruff check .` → **All checks passed!**；`ruff format --check .` → 0 待重排
- [x] 3.3 `pytest tests/graybox/unit tests/arch -q` → **153 passed**（112 + 新增 41）；`pytest tests/graybox/integration -q` → **16 passed**
- [x] 3.4 `--check-boundaries` → 零违规
- [x] 3.5 行数复扫：`views*.py` 全部 ≤ 291（`views_api_assets` 291 · `views_drf` 254 · `views_web` 240 · `views_pages` 236 · `views_page_elements` 196 · `views_projects_drf` 156 · `views_flows` 146 · `views_web_groups` 141 · `views_page_element_batch` 120 · `views_snapshot` 49）
- [x] 3.6 残余 `views.py` 字面引用仅剩 8 处 docstring 溯源注（「自 views.py 拆分」）+ 1 处 helper 溯源注，均**有意保留**

## 4. 过程中踩到并修掉的两个真坑（值得记下）

1. **装饰器被切到相邻分片**。按 `def name(` 取切片会漏掉其上的 `@csrf_exempt`：`batch_add_elements` 的装饰器滞留在上一片末尾，**静默套到了下一片的 `page_elements` 上**；`clear_pages` 的装饰器则滞留在批量片末尾（含裸 `@csrf_exempt` → SyntaxError）。
   **修法**：切片起点改为「优先匹配 `@csrf_exempt\ndef name(`」，并写了一个**装饰器审计脚本**：对每个新模块提取 `@csrf_exempt\ndef X` 集合，与**原文件的 23 处对照表**逐一比对，输出 `extra` / `missing`。修完 8 个模块全部 OK。
   **教训**：纯文本按行搬家必须把**装饰器纳入函数边界**；并且要用「原文件事实表 vs 新文件实际」自动比对，不能靠肉眼看 diff。

2. **中途重算分片时误判**：`views_page_elements.py` 首次生成 310 行（>300），再审时发现原文件内容已被上一步覆盖，无法再按原行号切片 → 改用「按函数名切片」+ 装饰器感知，并同步修正 `urls.py` 的 `clear_pages` 归属（它清空全部页面，属页面域而非元素域）。

## 5. 顺带查实的缺陷（本单不修，登记待办）

**4 个「分组写」视图函数是死代码**：`create_web_group` · `batch_move_web_groups` · `create_api_group` · `batch_move_api_groups`（共约 150 行）——
`urls.py` 已把 `web-groups/create` · `web-groups/batch-move` · `api-groups/create` · `api-groups/batch-move` 指向 `group_write_gone`（HTTP 410），这 4 个函数**全仓零引用**（实测 grep 仅命中自身定义与其调用的 `api.py` 同名函数）。本单保持「纯搬家」故未删；应另开死代码清理单。

## 6. 续做

1. **D3 写库收敛现在解锁了**：`views_*_drf.py` 的 `serializer.save()`（2 处）与 `api.py` 写函数返回 ORM（`create_web_element` / `update_web_element` / `create_web_page_flow`，被 `views.py` 原 6 处消费）现在分散在 8 个小模块里，可逐个收敛
2. 删除上述 4 个死视图函数（另单）
3. `api.py` / `api_directories.py` / `api_projects.py` 的体积与「返回 ORM」契约（另单）
