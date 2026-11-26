# Proposal: switch-ui-font-to-harmonyos-sans

## Why

需求方要求把平台页面字体换成米哈游官网的网页字体样式（参考图三张：知识库页现状 + 米哈游「关于米哈游」「加入米哈游」两屏）。

实测米哈游官网（`https://www.mihoyo.com/`，Nuxt 站点）的字体口径是**华为鸿蒙字体**：正文声明为 `font-family:HarmonyOS,Arial,Helvetica,sans-serif`，`@font-face` 指向 `fonts/HarmonyOS_Sans_SC_Thin.ttf`、`fonts/HarmonyOS_Sans_SC_Black.ttf`（大字标题用），即 **HarmonyOS Sans SC**（华为免费商用字体，开放 Thin/Light/Regular/Medium/Bold/Black 六档）。

当前平台实际渲染的并不是文档里写的「思源黑体」：`tokens.css` 的 `--font-body` 是 `PingFang SC → Microsoft YaHei → Noto Sans SC`，Windows 上第一、二位命中「微软雅黑」，而 Noto Sans SC 既没有 `@font-face` 也没有 CDN 引入，**从未真正加载**。因此「让人一眼看出换了字体」必须把字体文件带进本地，只改 `font-family` 名不会生效。

## What Changes

- 新增本地字体资产 `frontend/public/fonts/harmonyos-sans/`：华为官方发行包里的 **原始 TTF**——`HarmonyOS_SansSC_Regular/Semibold/Bold.ttf`（400/600/700，各约 8MB，合计 24.1MB），不做切片、不转 woff2、不裁字形；配 3 条 `@font-face`，随服务同源分发、断网可用。
- `frontend/index.html` 增加一条 `<link rel="stylesheet">` 挂载字体样式表（不进 entry CSS 包，避免撑爆 65KB 预算）。
- `frontend/src/shared/styles/tokens.css`：`--font-body` 首族改为 `HarmonyOS Sans SC`（回退链保留 PingFang SC / Noto Sans SC / Microsoft YaHei / system-ui）；`--font-brand` 首族仍是 `Ziku FeiYang`，仅回退链插入鸿蒙。
- 登记 Doodle Craft 主题偏离：`.agents/skills/doodle-craft/SKILL.md` 与 `references/tokens.md` 的「中文思源黑体 / Cascadia Mono」口径改为「中文鸿蒙黑体 HarmonyOS Sans SC + 等宽 Cascadia Mono」。
- 新增规格增量 `frontend-l0-design-tokens`：锁定「UI 字体由官方原版鸿蒙字体本地承载、品牌手写体保留、字号/字重刻度不因换字体改变」。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l0-design-tokens`：新增「全站 UI 字体由本地 HarmonyOS Sans SC 承载」要求。

## Impact

- **前端**：`frontend/index.html`、`frontend/src/shared/styles/tokens.css`、`frontend/src/views/LoginView.vue`（页脚字体声明，协议要求）；全站所有页面文字（含 Element Plus 组件，经 `--el-font-family` 继承）。
- **资产**：仓库新增 3 个官方 TTF（合计 24.1MB）+ 1 份 0.6KB CSS + 华为字体协议 `LICENSE_Fonts` + README；首屏按用到的字重下载（通常三档全下，约 24MB，之后缓存）。
- **不改**：字号 7 档、字重 5 档、行高、间距、圆角、颜色、组件皮肤；`Ziku FeiYang` 品牌手写体与登录页 Hero 版式。
- **不在范围**：`engines/ae_harness` 生成的 HTML 报告（自带独立字体表）、Swagger 页面、测试报告页的字体口径。
- **回退**：还原 `tokens.css` 两行 + 删除 `index.html` 的 link 即可立刻回到雅黑；字体目录可整体删除，无代码依赖。
