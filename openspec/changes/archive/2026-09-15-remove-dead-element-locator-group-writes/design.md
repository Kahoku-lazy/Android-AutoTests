## Context

「分组写」特性已在路由层下线（→410），但视图与 api 两层共 12 个函数仍留在代码里。上一个拆分单把 4 个视图函数标记为死代码，本单连同它们的 api 依赖一起删除。

## Goals / Non-Goals

**Goals:**

- 让代码层与路由层对「分组写已停用」这一事实一致
- 顺带把同一簇里**本就零调用**的 `rename_*` / `delete_*`（4 个）一并清掉，避免留下「半簇死代码」

**Non-Goals:**

- 不动 `group_write_gone`（410 出口）与两个 `*_group_detail` 的 410 分支
- 不动读路径（`list_web_groups` / `web_group_detail` GET / `_web_group_payload` 等）
- 不动 `api.py` 其他写原语（它们有真实调用方）

## Decisions

### 1. 删除范围取「整簇」而非只删用户点名的 4 个视图

- **选择**：4 视图 + 8 api 原语 = 12 个
- **理由**：实测这 12 个符号的**全部**命中只有自身定义与 `__all__` 条目。只删 4 个视图会留下 4 个「因本次删除而变死」的 api 函数（`create_*`/`batch_move_*`）与 4 个「本就死」的（`rename_*`/`delete_*`），下次读者仍要重新判定一遍。分节注释一并删，避免留下空标题

### 2. 保留 410 出口与读路径，并把出口修成真的 410

- **选择**：保留 `group_write_gone` 与 `*_group_detail` 的 410 分支；**并给 `group_write_gone` 补 `@api_view(["POST"])`**
- **理由**：410 是**有意**的产品决策（分组树写接口停用，改用项目目录 API），不是死代码；删了会变成 404/405，改变可观察契约。
  但实测它当时并**不是** 410 —— 裸 Django 视图返回 DRF `Response` 会在 `.render()` 时抛 `accepted_renderer not set` → **500**。
  本单既然要断言「仍 410」，就必须让它真的是 410；这也是「文档与代码保持一致优先」的直接要求

### 3. 用「符号已消失 + 仍 410」双向断言

- **选择**：测试同时断言 12 个符号不存在**与** 4 个写路径仍 410
- **理由**：只断言「不存在」会放过「顺手把 410 也删了」；只断言 410 会放过「没删干净」

## Risks / Trade-offs

- [误删仍有调用方的函数] → 已用 `grep <12 名字>` 于 `apps/` 全量核对：全部命中仅自身定义 + `__all__`；跨模块只消费 `ImportConflictError`/`import_snapshot_page`/`get_page_full`
- [`__all__` 是跨模块白名单] → 删除条目属公开面收窄；因零消费且特性已停用，风险为「未来需重新加回」，已在 Impact 说明
- [漏清 import] → `ruff check .` 的 F401 会拦；本单自己造成的死 import 必清

## Migration Plan

1. 删视图函数（2 文件）→ 删 api 原语与 `__all__` 条目（+2 分节注释）
2. `ruff check --fix` 清死 import；新增测试
3. 验证 `manage.py check` · `makemigrations --check` · ruff · 全量单测/集成 · `--check-boundaries`
4. 归档；回滚 = `git checkout` 三文件 + 删测试
