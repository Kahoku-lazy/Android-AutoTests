# device_inspector App CLAUDE.md

> 全局边界 / 协议要点 / 关单清单 → `../CLAUDE.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开。

## 红线（全局索引表 device_inspector 行的展开）

| 只做 | 禁止 |
|------|------|
| 屏幕快照抓取/保存/回看（v1.7 快照化 REST） | 恢复 WS 截图流（全局通道收敛硬约束） |
| 抓取元素落盘到 element_locator（经其 api） | 直连设备执行用例（设备读取经 device_pool api） |

- 截图流已快照化：前端拉快照而非订阅推送流，**任何变更不得重新引入 WS/推送截图**。
- OCR 与抓取逻辑在本 App `service.py`，禁止被其他 App import。

## 本 App 契约（特例 + 真相源）

真相源：`apps/device_inspector/urls.py`（7 端点：`capture` / `snapshots` / `snapshots/{id}` / `snapshots/{id}/analyze` / `snapshots/{id}/delete` / `snapshots/{id}/save-elements` / `pages/{id}`）+ `views.py` + `api.py`。

- `snapshots/{id}/analyze` 为纯规则结构分区（`algorithms/layout.classify_structure`），基于已存快照即时计算、不落库、无设备交互、无 LLM。

- 信封走全局标准 `{status, data}`；快照文件落盘路径与前端拉取路径是双边契约。
- `save-elements` 写元素资产必须经 `element_locator` 的 api 封装，禁止本 App 直接 ORM 写 `el_` 表（防火墙 #2）。
- 设备列表消费 device_pool（跨 App 只读 Model 或经其 api 取列表）。

## 本 App 协议要点

**无 WS**（全局 2 个 WS 生产点均不在本 App）。快照回看走 REST。

## 关单附加项（全局清单的 delta）

```
[ ] 无新增 WS consumer；grep 无 ws/ 路由注册
[ ] save-elements 写 el_ 表经 element_locator api（--check-boundaries 通过）
[ ] OCR/抓取耗时调用不阻塞事件循环（同步视图内保持既有约定）
```
