# element_locator App AGENTS.md

> 全局边界 / 协议要点 / 关单清单 → `../AGENTS.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.1 · 最后更新：2026-09-09 · v1.1：项目化（系统三项目 + 统一目录）。

## 红线（全局索引表 element_locator 行的展开）

| 只做 | 禁止 |
|------|------|
| 系统三项目下目录/文件 CRUD：Android 页面、Web 元素、API 端点 | 执行用例；增删改系统项目 |
| dump 结构、`ApiEndpoint` 契约维护 | 随意改 dump 字段；用分组树写接口做工作台编辑 |

- **dump 前缀字段是消费契约**：改结构必须三边同步。
- `page_tree.py` / `api_snapshot.py` 禁止被其他 App import；写库走本 App api。
- 系统项目 `android` / `web` / `api` 不可新建/改名/删除。

## 本 App 契约（特例 + 真相源）

真相源：`urls.py`（`projects` / `directories` / `move` / `files/batch-delete` + 叶子资源 + legacy）。

- **新工作台路径**标准信封 `{status, data}`。
- **legacy** `pages`/`items`/`web*`/`api-*` 平铺信封仍登记；禁止新增平铺路径。
- **分组写**（`web-groups`/`api-groups` create/update/delete/batch-move）→ HTTP 410。
- 叶子创建 body 可带 `directory_id`；页面显式传 `directory_id`（含 null）走工作台挂接。

## 本 App 协议要点

无 WS / SSE。素材被 workflow、device_inspector（导入）跨模块只读/经 api 写消费。

## 关单附加项

```
[ ] 改 dump/树结构 → 已同步消费方
[ ] 项目写接口 405；分组写 410
[ ] 迁移后叶子 ID 可仍按旧 id 读取
[ ] 跨 App 无直接 import page_tree/api_snapshot
```
