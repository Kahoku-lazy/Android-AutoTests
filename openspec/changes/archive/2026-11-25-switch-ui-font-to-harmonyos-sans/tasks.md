# Tasks: switch-ui-font-to-harmonyos-sans

> 2026-11-25 决策变更：第一版按 unicode-range 切片（246 个 woff2 + 391.6KB CSS）落地后，需求方确认「切片/转码是否属于协议禁止的修改」有解释空间，改为**官方原版 TTF、零改写**。切片产物已整体移除。

## 0. 前置核对

- [x] 0.1 确认参考站字体口径：`https://www.mihoyo.com/` 的 `_nuxt/ca7e4d8.js` 内含 `font-family:HarmonyOS,Arial,Helvetica,sans-serif` 与 `fonts/HarmonyOS_Sans_SC_Thin|Black.ttf`
- [x] 0.2 确认现状真渲染：`tokens.css` 原 `--font-body` 首族 `PingFang SC`，Windows 落到微软雅黑；全仓无 Noto Sans SC 的 `@font-face`/CDN 引入
- [x] 0.3 确认字体授权：HarmonyOS Sans Fonts License Agreement（免费商用，附四条条件）；华为协议原文 `LICENSE_Fonts` 随资产入库

## 1. 字体资产（官方原版 TTF）

- [x] 1.1 从华为官方包取原始 TTF：`HarmonyOS_SansSC_Regular/Semibold/Bold.ttf` → `frontend/public/fonts/harmonyos-sans/`
  - 实测：8.09 / 8.02 / 7.99MB，合计 24.11MB；`name` 表 Version 2.400、Copyright 2021-2025 Huawei Device Co., Ltd.；未做任何改写
- [x] 1.2 `harmonyos-sans.css`：3 条 `@font-face`（0.6KB），显式 `font-family:"HarmonyOS Sans SC"` + 400/600/700 + `format("truetype")` + `font-display:swap`
  - 注意：官方 Semibold 文件内部族名是 `HarmonyOS Sans SC Semibold`，必须显式声明字重，不能靠内部名
- [x] 1.3 写入 `LICENSE_Fonts`（华为 HarmonyOS Sans Fonts License Agreement 原文）与 `README.md`（v2.400、官方来源、文件清单、许可四条、体积、升级步骤）
  - 包自带的 `LICENSE` 是打包脚本的 Unlicense（不覆盖字体），已删除，只保留华为协议
- [x] 1.4 移除第一版切片产物（246 个 woff2 + 391.6KB 合并 CSS），目录只剩 3 个 TTF + 1 份 0.6KB CSS
  - 实测：`(Get-ChildItem ... -Filter *.woff2).Count` = 0

## 2. 接入

- [x] 2.1 `frontend/index.html` `<head>` 挂 `<link rel="stylesheet" href="/fonts/harmonyos-sans/harmonyos-sans.css" />`
  - 实测：`frontend/dist/index.html` 含该 link；`dist/fonts/harmonyos-sans/` 有 CSS + 3 个 TTF
- [x] 2.2 `tokens.css`：`--font-body` 首族 `"HarmonyOS Sans SC"`；`--font-brand` 回退链插入鸿蒙，首族仍是 `"Ziku FeiYang"`
  - 实测：`--font-mono`、字号 7 档、字重 5 档、行高、间距逐字未变
- [x] 2.3 字体声明未进 entry CSS
  - 实测：`python -m utils.check_bundle_budget` → `entry_css_kb 55.4 / 65 ok`（其余三项同样 ok）
- [x] 2.4 `views/LoginView.vue` 页脚追加「字体 HarmonyOS Sans SC」（协议第①条「软件内显著声明」的落点）
  - 判据：登录页底部可见该声明；`login/p0` 57 条用例全过

## 3. 文档登记（Doodle Craft 偏离）

- [x] 3.1 `SKILL.md`「一段话说清风格」改为「UI 字体一套（中文与西文统一鸿蒙黑体，代码与编号用 Cascadia Mono 等宽）」
- [x] 3.2 `references/tokens.md` §1.5 全局字体说明重写并加 2026-11-25 变更登记（顺带删掉指向不存在 `TestCaseBlockly.vue` 的过时提示）
- [x] 3.3 规格增量 `specs/frontend-l0-design-tokens/spec.md`（官方原版 TTF 本地承载、不切片不转码、品牌字保留、刻度不变、entry CSS 预算）

## 4. 验证

- [x] 4.1 `npm run lint:styles`：批 1/2/3/4 全通过，无新增命中
- [x] 4.2 `npx vue-tsc --noEmit`：通过（exit 0）
- [x] 4.3 `npm run build`：通过（29.0s）；`dist/index.html` 有 link、`dist/fonts/harmonyos-sans/` 为 3 个 TTF + CSS
- [x] 4.4 Playwright（Edge channel）以 `e2e_probe` 登录后核对：
  - `body` / `.wb-shell` 计算字体首族 = `HarmonyOS Sans SC`；`.brand-title` / `h1` 首族仍 = `Ziku FeiYang`
  - `document.fonts` 里 HarmonyOS 只有 3 个 face，状态全部 loaded；`document.fonts.check('14px "HarmonyOS Sans SC"')` = true
  - 网络请求：`HarmonyOS_SansSC_Regular/Semibold/Bold.ttf` 三个本地 TTF，无第三方字体域名
- [x] 4.5 截图：登录页、仪表盘、知识库、设备管理、任务清单、用例管理、BUG 单、测试报告，均无 `documentElement` 横向溢出
- [x] 4.6 `npm run test:p0`：81 个文件 / 495 条用例全过
- [x] 4.7 `python -m run check`：28/30 阻塞项通过；2 个失败均为工作区既有改动（`ai-assistant/eval-cases.vue`、`evals.vue` 的 prettier 格式与 `evals.vue` 506 行 > 500），与本次字体改动无关
- [x] 4.8 `npx vitest run tests/login/p0` 57 条全过；`eslint` 0 问题；`prettier --check` 对本单文件全过

## 5. 收口

- [x] 5.1 `npx openspec validate switch-ui-font-to-harmonyos-sans` → valid
- [x] 5.2 `git status` 核对：本次只新增/改动 `frontend/index.html`、`frontend/src/shared/styles/tokens.css`、`frontend/src/views/LoginView.vue`、`frontend/public/fonts/harmonyos-sans/**`、两篇技能文档与变更单
  - 注意：工作区在我接手前已有 179 个未提交改动（ai-assistant / project-viz 等其它在工作），**未做任何提交**，也未碰那些文件
- [x] 5.3 交付说明写清：采用「全站 UI 换官方原版鸿蒙字体 + 保留手写品牌字 + 只换字族」，并给出回退两步
