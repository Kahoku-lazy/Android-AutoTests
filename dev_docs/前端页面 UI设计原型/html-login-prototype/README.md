# 登录页 HTML UI 原型（Web 桌面）

纯静态 HTML/CSS/JS，对齐 `../01-登录页.md` 与现网 `LoginView`（Doodle Craft / Meeting doodle）。

本目录是 **Web 桌面原型**：对照板与交互演示均用**浏览器窗口框**展示桌面 Hero 双栏布局（约 1280×800 / 流体视口），**不是手机壳 / 手机产品形态**。

上级目录 `参考-UI对照板风格.png` **仅作板式参考**（紫条分区、黄便签批注、当前/更新后对照、页面跳转流程），不是移动端产品目标。

## 如何打开

任选其一：

1. **直接打开**：用浏览器打开本目录下的 `index.html`（`file://` 即可）。
2. **本地静态服务**（推荐，避免个别浏览器限制 localStorage）：

```powershell
cd "D:\GitHub\Android-AutoTests\dev_docs\前端页面 UI设计原型\html-login-prototype"
python -m http.server 8765
```

浏览器访问：<http://127.0.0.1:8765/>

## 页签说明

| 页签 | 内容 |
| --- | --- |
| **对照板 · 跳转流程** | 多行紫条分区：布局、模式切换、校验态、提交结果、路由守卫、可选增强；黄便签批注；**浏览器窗**标注「当前 / 更新后 / 交互态」 |
| **流程高亮图** | SVG 跳转图；按钮高亮：守卫、成功、模式切换、Overlay、Token 过期 |
| **交互演示** | 桌面登录/注册双栏（左 Hero + 右 Meeting doodle）；可点表单、记住账号、回车提交、Mock 成功/失败 Overlay、一键场景 |

## 可点击流程

- 登录 ↔ 注册（左栏 CTA +「去注册/去登录」）
- 字段即时校验（文案与文档一致）；非法时提交禁用
- Enter 提交；loading → Toast 成功并进入工作台 Mock，或 Overlay 错误
- 记住账号：`localStorage.proto_saved_username`（原型键，非生产 `saved_username`）
- 一键：登录成功 / 401 / 网络失败 / 注册成功 / 用户名已存在 / Token 过期回流
- 对照板便签上的「高亮跳转流」会切到流程图并标红路径

## Mock 账号

| 输入 | 结果 |
| --- | --- |
| 用户名 `fail` 或密码 `wrong` | Overlay：用户名或密码错误 |
| 用户名 `network` | 网络连接失败，请稍后重试 |
| 用户名 `down` | 后端服务未就绪… |
| 注册用户名 `exists` | 用户名已存在 |
| 其它通过校验的输入 | 成功并跳转工作台 Mock |

## 文件

- `index.html` — 对照板 + 流程图 + 交互演示
- `styles.css` — 板式 chrome（浏览器窗）+ Doodle Craft 近似样式
- `app.js` — 页签 / 流程高亮 / Mock 表单
- `README.md` — 本说明

## 注意

- 不调用真实 `/api/auth/*`；不修改应用运行时代码。
- 勿将本目录中的 mock token / 用户名当作真实密钥。
- ≤768px 单列仅为响应式行为说明，原型交付形态是桌面 Web 页。
