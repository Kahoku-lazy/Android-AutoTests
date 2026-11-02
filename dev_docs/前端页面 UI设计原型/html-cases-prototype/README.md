# 用例管理 HTML UI 原型（Web 桌面）

对齐 `../09-用例管理.md` 与 `modules/case-manager`。

```powershell
cd "D:\GitHub\Android-AutoTests\dev_docs\前端页面 UI设计原型\html-cases-prototype"
python -m http.server 8773
```

访问 <http://127.0.0.1:8773/> 或直接打开 `index.html`。

## 路由

- `/cases` — 用例管理
- `/cases/projects/:projectId` — 项目工作台
- `/cases/projects/:projectId/files/:fileId` — 编辑用例表

需求文档：[09-用例管理.md](../09-用例管理.md)
