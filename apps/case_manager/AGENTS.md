# case_manager App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 case_manager 行的展开）

| 只做 | 禁止 |
|------|------|
| 用例定义编排：UI/API/Web/Storage 四类定义 + 目录树 | 执行完整任务（调试单步经 test_runner `run-step`） |
| 编辑锁逻辑（`api_lock.py`）+ 锁状态 WS 推送 | 在 consumer 里改锁状态（写库仍走 api） |

- **`config_json` / 步骤结构与 test_runner 执行器字段严格对齐**——改用例结构不同步执行器，症状是「保存成功但执行失败」。
- 目录树 `case_type` 区分四类定义，改目录/定义归属不得混 type。
- 本 App 文件多（`api*.py` × 8、`views*.py` × 8、`models*.py` × 4），拆分边界已定：`api_ui/api_web/api_api/api_storage` 对应四类定义，`api_directories` 目录，`api_lock` 锁；新增功能归入既有对应文件，禁止再开并列大文件。

## 本 App 契约（特例 + 真相源）

真相源：`apps/case_manager/urls.py`（router：`directories` / `definitions` / `storage/definitions` / `api-testing/definitions` / `web/definitions` + 手动注册 lock/unlock/visibility + legacy 平铺路径）+ `serializers.py`。

- **信封双口径**：router 路径（`directories`/`definitions` 系列 ViewSet）走全局标准 `{status, data}`；**legacy 平铺路径**（`views_base.py`/`views_directories.py`/`views_lock.py`/`views_ui.py` 等 JsonResponse：`definitions`/`directories`/`lock`/`unlock` 等）为平铺 `{status, definitions|tree|definition|...}`（`step-types` 特例 `{status, data:{types}}`；已登记 2026-08-21 校验结论，禁止新增平铺路径，未收敛前禁止改造成信封式）。
- 锁端点三态：`lock`（编辑锁）/ `case-lock`（硬锁）/ `visibility`；router 与 legacy 两套路径共存，行为一致。锁请求体契约：`unlock` body `{force}`；`visibility` body snake_case `permitted_users`（与前端 case-manager 模块已登记口径一致，改字段双边同步）。
- test_runner 跨模块只读用例定义（`/cases/definitions` 系列消费方）。

## 本 App 协议要点

**WS（本 App 专属，全项目仅 2 个 WS 生产点之一）**：`/ws/case-editing/{case_id}`

- `consumers.py` 服务端推送单一事件 `case_updated`（经 group_send，`receive` 只做 keep-alive）。
- 锁状态变更 → `api_lock.py` 写库 → 再推送 `case_updated`；**推送顺序与锁状态必须一致**，前端以推送驱动只读禁用。
- 新增事件 type 必须同步全局 `../AGENTS.md` §2 + 前端 `case-manager/AGENTS.md`（双边契约）。

## 关单附加项（全局清单的 delta）

```
[ ] config_json/步骤结构变更已同步 test_runner 执行器 + 前端编辑器
[ ] 锁：acquire/release/hard-lock 三条路径 + WS 推送 case_updated 覆盖
[ ] router 与 legacy 双路径同改
[ ] consumer 无 ORM 写（写库走 api_lock）
```
