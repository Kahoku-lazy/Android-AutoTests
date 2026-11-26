# Proposal: land-harmonyos-sans-font

## Why

`2026-11-25-switch-ui-font-to-harmonyos-sans` 在 2026-11-25 已归档（tasks 17/17），但它的**代码与规格增量一直没落进主干**：
`origin/Kahoku` 的 `tokens.css` 仍是 `Cascadia Mono + Noto Sans SC`，`index.html` 仍挂着 `fonts.googleapis.com` 的远端样式，
`frontend-l0-design-tokens` 里也没有「UI 字体」这条要求。结果是需求方指定的鸿蒙字体只在某台机器的本地工作区里生效。

需求方 2026-11-26 另有一项裁决改变落地方式：**字体二进制不入库**（24.1MB），改为「本地缺失就自动取用」。
因此不能照搬归档单的三件 TTF，需要把「资产」换成「取用机制」。

## What Changes

- 字体接线（照归档单落地）：`tokens.css` 的 `--font-body` / `--font-brand` / `--font-mono`；
  `index.html` 用本地 `/fonts/harmonyos-sans/harmonyos-sans.css` 替换 Google Fonts 三行；
  `style.css` 品牌字改 woff2 优先并删掉两条 jsDelivr 的 Cascadia `@font-face`；`LoginView` 页脚声明字体
- 资产：只入库 `harmonyos-sans.css` / `README.md` / `LICENSE_Fonts` 与品牌字 `ziku-feiyang.woff2`（795KB）；
  三个 TTF 由 `.gitignore` 排除（该规则已随 `#76` 落库）
- 取用机制：新增 `utils/fetch_fonts.py`（幂等、`--soft` 软失败、断网给可操作提示），
  接到 `frontend/package.json` 的 `predev` / `prebuild` 与 `utils/service_ctl` 的 frontend `preflight`
- 规格：给 `frontend-l0-design-tokens` 补「全站 UI 字体由本地官方原版 HarmonyOS Sans SC 承载」要求（7 个场景），
  其中「不入库 + 按需取用 + 取不到不阻断」是本次新增的口径
- 技能口径：`doodle-craft` 的 `SKILL.md` 与 `references/tokens.md` 同步字体口径

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增「UI 字体由本地鸿蒙原始 TTF 承载、二进制不入库、缺失按需取用」要求

## Impact

- 前端：`index.html`、`src/style.css`、`src/shared/styles/tokens.css`、`src/views/LoginView.vue`
- 资产与工具：`frontend/public/fonts/harmonyos-sans/*`（3 个文本文件 + 3 个被忽略的 TTF）、`ziku-feiyang.woff2`、
  `utils/fetch_fonts.py`、`frontend/package.json` 两个 hook、`utils/service_ctl/{config,services}.py`、`ruff.toml` 一条 per-file-ignore
- 文档：`doodle-craft` 两处口径
- 运行时：首次 `npm run dev` / `npm run build` / `run start frontend` 会尝试下载约 59MB 发行包（之后复用缓存）；
  取不到只警告，页面回退系统字体
- CI：**不下载字体**——`check_gates.py` 直接 `npx vite build`，不触发 npm 的 `prebuild`，字体也不在 JS/CSS 包里
- 回退：还原 `tokens.css` 三行 + `index.html` 一行链接 + 删 `utils/fetch_fonts.py` 与两处 hook，即可回到雅黑
