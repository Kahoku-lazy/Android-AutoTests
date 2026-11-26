# Tasks: land-harmonyos-sans-font

> 格式：**动作 → 完成判据**。

## 1. 字体接线

- [x] 1.1 `frontend/src/shared/styles/tokens.css`：`--font-body` 首族改 `HarmonyOS Sans SC`（回退 PingFang SC / Noto Sans SC / 微软雅黑 / system-ui）；`--font-brand` 回退链插入鸿蒙；`--font-mono` 改 `Consolas / Cascadia Mono / ui-monospace` 系统栈。
  判据：diff 只动这三处；`lint:styles` 无新增命中（frontend 门禁 `style-gates` PASS）。
- [x] 1.2 `frontend/index.html`：删 Google Fonts 两行 `preconnect` 与一条 `css2` 样式表，改挂 `/fonts/harmonyos-sans/harmonyos-sans.css`。
  判据：`googleapis` 命中 0；`dist/index.html` 含本地字体样式表链接。
- [x] 1.3 `frontend/src/style.css`：品牌字 `@font-face` 改 `woff2` 优先 + `ttf` 兜底；删两条 jsDelivr 的 Cascadia `@font-face`。
  判据：`jsdelivr|Cascadia Mono` 命中 0。
- [x] 1.4 `frontend/src/views/LoginView.vue`：页脚声明当前字体。
  判据：页脚文案含 `HarmonyOS Sans SC`（命中 1）。

## 2. 资产与取用

- [x] 2.1 入库 `frontend/public/fonts/harmonyos-sans/{harmonyos-sans.css,README.md,LICENSE_Fonts}` 与 `frontend/public/fonts/ziku-feiyang.woff2`。
  判据：`git ls-files frontend/public/fonts` 列出这 4 个 + 既有 `ziku-feiyang.ttf`，不含任何 harmonyos `.ttf`。
- [x] 2.2 新增 `utils/fetch_fonts.py`：缓存发行包到 `temps/cache/`、按名解出三档、按体积（≥8MB）校验、已就位即跳过、`--soft` 软失败、失败给可操作提示。
  判据：`python -m utils.fetch_fonts` → 打印「字体已就位」并退出 0；`ruff check` / `ruff format --check` 通过。
- [x] 2.3 `frontend/package.json` 加 `predev` / `prebuild`（`--soft`）；`utils/service_ctl` 的 frontend 加 `preflight` 并在 `start_service` 执行。
  判据：`python -m run restart frontend` 的输出里，启动 Vite 之前出现「字体已就位」，随后 ready。
- [x] 2.4 `ruff.toml` 的 utils per-file-ignore 名单加 `fetch_fonts`（T201，与既有 CLI 脚本同口径）。
  判据：`ruff check utils/fetch_fonts.py` 通过。

## 3. 规格与文档

- [x] 3.1 delta 拆成两条要求（字体承载 / 二进制不入库与按需取用）+ 7 个场景，避免单条要求超 500 字。
  判据：`openspec validate land-harmonyos-sans-font --strict` → `is valid`（退出码 0）。
- [x] 3.2 `doodle-craft` 的 `SKILL.md`（一段话风格句）与 `references/tokens.md`（字体段 + 2026-11-25 变更说明）同步鸿蒙口径。
  判据：两文件内 `HarmonyOS Sans SC` 已写入，正文族不再指向思源黑体。

## 4. 门禁与验收

- [x] 4.1 前端门禁十条全过。
  判据：`utils/check_gates.py --only …` 十项全 PASS。
- [x] 4.2 运行时验收。
  判据：`dist/fonts/harmonyos-sans/` 含样式表 + 三档 TTF；预览服 `GET /fonts/harmonyos-sans/HarmonyOS_SansSC_Regular.ttf` → `200 8483132 font/ttf`。
- [x] 4.3 `openspec validate --all` 与 python 门禁 20 条全过。
  判据：`validate --all` → 170 passed / 0 failed；python 门禁 20/20。
