# AI 助手 HTML UI 原型（Web 桌面）

纯静态 HTML/CSS/JS，对齐 `../03-AI助手.md` 与现网 `modules/ai-assistant`（Doodle Craft）。

本目录是 **Web 桌面原型**：对照板与交互演示均用**浏览器窗口框**展示侧栏 + 主区工作台，**不是手机壳**。

## 如何打开

1. **直接打开**：用浏览器打开本目录下的 `index.html`（`file://` 即可）。
2. **本地静态服务**（推荐）：

```powershell
cd "D:\\GitHub\\Android-AutoTests\\dev_docs\\前端页面 UI设计原型\\html-ai-assistant-prototype"
python -m http.server 8767
```

浏览器访问：<http://127.0.0.1:8767/>

## 页签说明

| 页签 | 内容 |
| --- | --- |
| **对照板 · 跳转流程** | 紫条分区 + 黄便签 + 浏览器窗「当前 / 更新后 / 交互态」 |
| **流程高亮图** | SVG 跳转图；按钮高亮关键路径 |
| **交互演示** | 桌面侧栏 + 主区 Mock；可点主流程 |

## 主路由

- `/ai-assistant` — 重定向
- `/ai-assistant/agents` — 平台小助手
- `/ai-assistant/agent/:agentId` — 智能体详情

## 文件

- `index.html` / `styles.css` / `app.js` / `README.md`

## 注意

- 不修改应用运行时代码；勿提交敏感真实环境数据。
- 需求文档：[03-AI助手.md](../03-AI助手.md)
