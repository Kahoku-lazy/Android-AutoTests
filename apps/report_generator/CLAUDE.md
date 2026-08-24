# report_generator App CLAUDE.md

> 全局边界 / 协议要点 / 关单清单 → `../CLAUDE.md`；本文只写本 App 增量，冲突以全局为准。
> 版本：v1.0 · 最后更新：2026-08-21 · v1.0：从已归档 `dev_docs/_archive/后端claude笔记.md` §0️⃣ 模块表迁出并展开；登记信封特例。

## 红线（全局索引表 report_generator 行的展开）

| 只做 | 禁止 |
|------|------|
| 报告只读聚合/详情/分解 + 下载（文件由 test_runner 落盘） | 写业务数据（跨 App 写必须走对方 api） |
| `FileResponse` 下载报告文件 | 把文件内容塞进 JSON 信封 |

- **本 App 只读**：报告文件由 test_runner 生成落盘，本 App 只读盘 + 查询聚合。
- 下载/查看端点必须防路径穿越（`{filename}` 校验），现有 403/404 语义保持。

## 本 App 契约（特例 + 真相源）

真相源：`apps/report_generator/urls.py`（6 端点：`""` / `cases` / `run/{run_id}` / `task/{task_id}` / `{filename}/content` / `{filename}`）+ `views.py` + `api.py`。

**信封特例（legacy 平铺，禁止新增/改造，已登记 ARCH-07）**：

- `/reports/*` 列表/详情响应为**平铺** `{status, ...}`（非全局 `{status, data}`），前端按平铺读取。
- 下载走 `FileResponse`（`{filename}` 端点），前端用 `fetch().text()` 消费，**不是 JSON 信封**——改形状前端解析即崩。
- `{filename}/content` 为 HTML 内容查看端点。

## 本 App 协议要点

无 WS / SSE。

## 关单附加项（全局清单的 delta）

```
[ ] 无 ORM 写业务表；只读查询 + 文件读取
[ ] 路径穿越防护：恶意 filename 返回 403/404（不落盘、不泄漏）
[ ] 平铺信封与 FileResponse 形态未变（前端按平铺/文本读取）
```
