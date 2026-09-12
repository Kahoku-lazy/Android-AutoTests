# case-manager 模块 AGENTS.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../AGENTS.md`；本文只写本模块增量，冲突以全局为准。
> 版本：v2.1 · 2026-09-09 · 目录树 + 文件 Excel 编辑。

## 红线

| 只做 | 禁止 |
|------|------|
| 项目列表、工作台仅目录树、点文件进表格页 | 执行用例 / 四类型可执行编辑器 / 预览面板 / 工作台右侧表单 |
| 经模块 `api.ts` → djangoClient | 直连后端端口、旁路 axios |

## 本模块契约

真相源：`api.ts` + `types.ts` + `routes.ts`

- `/cases` 项目列表 · `/cases/projects/:id` 仅目录树 · `/cases/projects/:id/files/:fileId` Excel 表
- `GET/POST /cases/projects/` · `PATCH/DELETE /cases/projects/{id}/` · `GET .../tree/`
- `POST/PATCH/DELETE /cases/directories/`
- `POST/GET/PATCH/DELETE /cases/files/`（GET 返回 `{file, rows}`）
- `POST/GET/PATCH/DELETE /cases/definitions/` · `POST .../batch-delete/`
- `POST /cases/move/`（`item_type`: `directory` | `file`）
- 信封 `{status, data}`；字段 snake_case

## 协议要点

无 WS。编辑锁通道已下线。

## 关单附加项

```
[ ] 进项目只见目录/文件；点文件才进表格
[ ] 表格列：测试类型/业务类型/时间/标题/模块/前置/步骤/预期；支持新建行
[ ] 脏数据离开确认；侧栏单项 /cases；旧四路径 redirect
```
