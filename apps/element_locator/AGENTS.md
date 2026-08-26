# element_locator App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 element_locator 行的展开）

| 只做 | 禁止 |
|------|------|
| 三域资产 CRUD：UI 页面/元素、Web 元素/组、API 组/端点 | 执行用例（消费方是 test_runner/case_manager 调试） |
| dump 结构、`ApiEndpoint` 契约维护 | 随意改 dump 字段/树结构（前端树与定位全崩） |

- **dump 前缀字段是消费契约**：device_inspector 抓取、case_manager 展示、test_runner 定位都按 dump 结构消费；改结构必须三边同步，否则「保存成功但定位失败」。
- `page_tree.py` / `api_snapshot.py` 是内部实现，禁止被其他 App import；其他 App 读资产走只读 Model 或本 App api。

## 本 App 契约（特例 + 真相源）

真相源：`apps/element_locator/urls.py`（DRF router：`web-groups` / `web` / `api-groups` / `api-endpoints` / `flows` / `web-flows` + legacy：`pages` / `items` / `web*` / `api-*`）+ `views.py` / `views_drf.py` + `serializers.py`。

- **router 与 legacy 双路径共存**：同一资产两套端点，行为必须一致；改一处漏另一处 → 前端旧页面 404 或数据不同。
- **信封双口径**：router 路径（`web-groups`/`web`/`api-groups`/`api-endpoints`/`flows`/`web-flows`）走全局标准 `{status, data}`；**legacy 路径（`pages`/`items`/`web*`/`api-*`，`views.py` JsonResponse）为平铺** `{status, pages|elements|groups|flows|endpoint|...}`（已登记 2026-08-21 校验结论，禁止新增平铺路径，未收敛前禁止改造成信封式）。
- `ApiEndpoint`（method/path/params 等）字段是 api-testing 用例引用的真相源，禁止无迁移改字段。

## 本 App 协议要点

无 WS / SSE。素材被 workflow（画布引用）、case-manager（用例步骤引用）跨模块只读消费。

## 关单附加项（全局清单的 delta）

```
[ ] 改 dump/树结构 → 已同步 device_inspector、case_manager、test_runner 消费方
[ ] router 与 legacy 双路径同改（新增/删除/改字段）
[ ] ApiEndpoint 字段变更含 migration + 前端契约同步
[ ] 跨 App 消费方无直接 import page_tree/api_snapshot
```
