# workflow App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开；登记信封特例。

## 红线（全局索引表 workflow 行的展开）

| 只做 | 禁止 |
|------|------|
| 编排目录/文档 CRUD（VueFlow 画布数据） | 执行编排（编排只定义，不跑流程） |
| 编排语义在 `semantics.py` / `semantics_paths.py` 内部维护 | 外部模块直接篡改编排状态/语义字段 |

- 编排状态勿被外部直接篡改：跨 App 读可走 Model，写必须走本 App api。
- 素材（element_locator 资产）只读引用，禁止本 App 反向写 `el_` 表。
- 前端 workflow 模块是 3 个 Pinia store 用户之一（`wf-workflow` / `wf-library`），字段契约以 Serializer 为准。

## 本 App 契约（特例 + 真相源）

真相源：`apps/workflow/urls.py`（router：`directories` / `documents` + legacy 平铺路径）+ `views.py` / `views_api.py` + `serializers.py`。

**信封特例（legacy 平铺，禁止新增/改造，已登记 ARCH-09）**：

- legacy 路径（非 router 路径）响应为**平铺** `{status, directory|document|documents|...}`，非全局 `{status, data}`。
- router 路径（`directories` / `documents` ViewSet）走全局标准信封；**两套路径并存，行为必须一致**。

## 本 App 协议要点

无 WS / SSE。

## 关单附加项（全局清单的 delta）

```
[ ] legacy 与 router 双路径同改，行为一致
[ ] legacy 平铺信封保持（未收敛前不改造成信封式）
[ ] 语义字段改动含 migration + 前端 VueFlow 契约同步
[ ] 无反向写 el_ 表（素材只读引用）
```
