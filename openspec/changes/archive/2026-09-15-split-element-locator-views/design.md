## Context

1357 行的 `views.py` 已是 calibration §4 的 🔴（4.5×），且挡住 D3 写库收敛。文件内部本就有 8 个 `# ──` 分段，拆分即「让文件边界追上既有的代码边界」。

## Goals / Non-Goals

**Goals:**

- 每个 `views*.py` ≤ 300 行（§4 上限），并用测试钉住防回涨
- 把 `views.py` 的隐式写路径与 ORM 返回纠缠**拆散**，为后续 D3 收敛铺路
- 零行为变化

**Non-Goals:**

- 不改任何函数体、不改路由、不改信封
- 不收敛写路径（本单只搬家）
- 不动 `views_drf.py` / `views_projects_drf.py` 的既有逻辑（它们已是上一轮拆分的产物）

## Decisions

### 1. 按文件自带的段边界拆，不发明新分类

- **选择**：7 个新模块对应原有 8 个 `# ──` 段（仅 Page CRUD 因超 300 行拆成 pages / page_elements）
- **理由**：拆分应「发现」已有边界而非「发明」新边界 —— 这样 diff 是纯平移，reviewer 可逐段核对；也避免与 `views_drf.py` / `views_projects_drf.py` 的既有命名冲突

### 2. 删 `views.py`，不留转发壳

- **选择**：`urls.py` 直接改导入新模块
- **理由**：唯一消费方就是 `urls.py`（实测），改它零风险；转发壳是为「多个既有调用方」准备的（见 `apps/device_pool/AGENTS.md` 的兼容层定义），此处不成立，留壳只增间接层

### 3. `_optional_directory_id` 迁到 `api_directories.py` 并转公有

- **选择**：改名 `optional_directory_id(data, *, project_code)`，登记 `__all__`
- **理由**：两个视图片需要它，留在任一片都会造成「视图模块互相 import」；它做的事是「校验 directory_id 属于该 project」（`LocatorDirectory` 查询），属目录域 —— 归 `api_directories.py` 比新造 `helpers.py` / `common.py` 更符合「不过早万能 helpers」与命名空间隔离

### 4. 放宽 `gen_arch_stats` 的 `has_views`

- **选择**：`(d / "views.py").exists() or any(d.glob("views*.py")) or (d / "views").is_dir()`
- **理由**：`has_views` 只喂生成报告（行 638/878 的 ✅/❌），逻辑上「有视图模块」才对；不改它，element_locator 拆分后会在报告里显示 ❌「无视图」。顺带修正 `ai_assistant` / `case_manager`（只有 `views_*.py`）这两处本就错的 ❌

### 5. 用 `resolve()` + 行数上限做回归门禁

- **选择**：新测试断言 ① 代表路径仍解析到同名函数（legacy 与 router 各覆盖）；② `element_locator/views*.py` 每片 ≤ 300 行
- **理由**：拆分最典型的失败是「路由悄悄失效」或「导入漏名」；`resolve()` 一次覆盖两者。行数断言把 §4 从「人工检查」变成「CI 会拦」

## Risks / Trade-offs

- [搬家漏名 / 漏 import] → `manage.py check` 会加载 URLconf（缺名即 NameError）；`resolve()` 测试逐条覆盖 34 个路径；`ruff check` 兜 F401
- [漏掉某个消费方] → 实测全仓只有 `urls.py` import 本文件（`views_drf.py:4` 只是 docstring 提到）
- [文件数变多] → 7 个域模块 vs 1 个 1357 行巨石；模块数增加是可读性的代价，且与文件内既有分段一一对应
- [报告口径变化] → `has_views` 放宽会让 2 个 App 的报告由 ❌→✅（更准确），并已在 proposal 登记

## Migration Plan

1. 建 7 个新模块（逐段平移 + 各自 import）
2. `api_directories.py` 加 `optional_directory_id`；两片 import 它
3. `urls.py` 改导入；删 `views.py`
4. 改 `gen_arch_stats.py` 与 3 处文档指向 + `views_drf.py` docstring
5. 新增回归测试；跑 `manage.py check` · `makemigrations --check` · ruff · 全量 unit/arch/integration · `--check-boundaries`
6. 归档；回滚 = `git checkout` 被改文件 + 删新模块 + 恢复 `views.py`
