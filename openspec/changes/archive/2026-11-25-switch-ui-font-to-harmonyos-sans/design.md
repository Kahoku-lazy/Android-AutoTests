# Design: switch-ui-font-to-harmonyos-sans

## Context

需求方指定参考米哈游官网的网页字体，并确认三项口径：**全站 UI 文字**（品牌手写体保留）、**本地交付**、**只换字族**（不动字重/字距/字号）。

参考站点字体已核实为 **HarmonyOS Sans SC**（`font-family:HarmonyOS` + `HarmonyOS_Sans_SC_Thin/Black.ttf`）。当前平台 `--font-body` 首族是 `PingFang SC`，Windows 落到「微软雅黑」，`Noto Sans SC` 无任何加载途径。

第一版实现用 `cn-font-split` 的 unicode-range 切片（246 个 woff2），需求方 2026-11-25 确认改为**官方原版 TTF、不做任何改写**，以消除「切片是否属于协议禁止的修改」的解释风险。

约束：

- 平台可能在内网/断网环境使用，字体必须同源本地分发，不能挂 CDN。
- `frontend/bundle-budgets.json` 的 `entry_css_kb` 预算 65KB（基线 55.4KB），字体声明不能进 entry CSS。
- 全仓不写注释；Doodle Craft 主题偏离须登记回技能参考。
- 字号/字重/行高/间距是 Doodle Craft 的既有刻度，本次不碰。

## Goals / Non-Goals

**Goals**

- 全站 UI 文字以本机文件渲染 HarmonyOS Sans SC，断网一致。
- 字体文件保持华为官方原始形态（unmodified），许可解释零风险。
- 品牌手写体、字号与字重刻度、组件皮肤零变化。

**Non-Goals**

- 不做米哈游式字重/字距再设计（用户已选「只换字族」，如需要另开一单）。
- 不改 `engines/ae_harness` HTML 报告、Swagger、测试报告页的字体。
- 不裁剪字形、不转 woff2、不切片。

## Decisions

### D1 用官方原版 TTF，不做任何改写

来源：华为官方发行包 `HarmonyOS-Sans-v2.zip`（58.8MB），解压路径 `HarmonyOS Sans/HarmonyOS_SansSC/`。取三档原始文件放入 `frontend/public/fonts/harmonyos-sans/`：

| 文件 | 字重 | 大小 | `name` 表族名 |
|---|---|---|---|
| `HarmonyOS_SansSC_Regular.ttf` | 400 | 8.09MB | `HarmonyOS Sans SC` / Regular |
| `HarmonyOS_SansSC_Semibold.ttf` | 600 | 8.02MB | `HarmonyOS Sans SC Semibold` / Regular |
| `HarmonyOS_SansSC_Bold.ttf` | 700 | 7.99MB | `HarmonyOS Sans SC` / Bold |

版本 Version 2.400，版权 `Copyright 2021-2025 Huawei Device Co., Ltd.`。

注意 Semibold 的内部族名带后缀，`@font-face` 必须显式写 `font-family: "HarmonyOS Sans SC"` + `font-weight: 600`，否则三档会被当成两个族。

### D2 三档字重：Regular(400) / Semibold(600) / Bold(700)

依据现有用量：`bold` 116 处、`heavy(800)` 82 处、`semibold(600)` 37 处、`medium(500)` 5 处、`regular(400)` 5 处（正文默认 400）。

- 官方包本身提供 Semibold，600 与 700 各有独立字面，37 处 semibold 不会被并到 bold。
- 不带 800：官方 800 档不存在（只有 900 Black）；现状微软雅黑同样没有 800 字面，`heavy` 一直由 Bold 渲染，观感不变。
- 500 由浏览器就近匹配到 400（5 处表单标签，差异可忽略）。

### D3 不切片、不转 woff2

协议第②条禁止对字体或其组件做修改。unicode-range 切片、ttf→woff2 转码都会改变字体二进制，解释风险由使用方承担；需求方选择零风险路径，因此：

- CSS 只剩 3 条 `@font-face`（0.6KB），不再有 391.6KB 的 unicode-range 表；
- 仓库文件从「246 个 woff2 + 1 份 CSS」降到「3 个 TTF + 1 份 CSS」；
- 代价：首屏从「按字符命中下载几十 KB」变成「用到的字重各下 8MB」（通常三档全下，约 24MB）；同源、内网、可缓存，可接受。

### D4 字体声明放 public 静态样式表，由 index.html 挂载

- 不进 `src/style.css`：字体声明是静态资产的一部分，与 TTF 同目录、同源同路径，开发态与生产态一致（`/fonts/harmonyos-sans/harmonyos-sans.css`），与既有 `/fonts/ziku-feiyang.woff2` 同一写法。
- 一份 CSS、三个 `@font-face`，没有构建期处理，`dist` 里原样存在。

### D5 `tokens.css` 只改两处字体族

```
--font-body: "HarmonyOS Sans SC", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif;
--font-brand: "Ziku FeiYang", "HarmonyOS Sans SC", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
```

`--app-font` / `--app-font-display` / `--el-font-family` 都是 `var(--font-body)` 的别名，自动跟随，无需逐处替换；`--font-mono`（Cascadia Mono/Consolas）保持不动，表格数字与代码仍是等宽。

### D6 品牌字保留

侧栏「智能化测试平台」、页头标题、登录页 Hero 继续用 `Ziku FeiYang`。只手写体缺字时回落到鸿蒙，避免出现雅黑混排。

### D7 首屏闪烁与回退

`font-display: swap`：字体未就绪时先显示回退字，命中后切换。断网/文件缺失时整链回退到 PingFang SC / 微软雅黑，页面功能不受影响。

### D8 协议四条与落点

| 条款 | 落点 |
|---|---|
| ① 软件内显著声明 | 登录页页脚「字体 HarmonyOS Sans SC」（`views/LoginView.vue`） |
| ② 不得修改 | 只放官方原始 TTF，CSS 仅做 `@font-face` 引用 |
| ③ 不得单独再分发 | 字体只随平台 `public/` 分发，无独立下载入口 |
| ④ 保留版权与协议 | 字体内嵌版权字符串保留；`LICENSE_Fonts` 随目录入库并进入 `dist` |

## Risks / Trade-offs

- **[首屏 8–24MB 字体流量]**：三档 TTF 各约 8MB，首次访问按用到的字重下载。缓解：内网/本机场景可接受；`dist` 与 dev 均由浏览器缓存；如要压体量，可只保留 400 + 700 两档（约 16MB，600 会并到 700）。
- **[首屏 FOUT]**：`swap` 期间可能看到一次雅黑→鸿蒙的切换。缓解：CSS 在 `<head>` 阻塞加载，通常只影响首帧；不引入 FOIT 以免白屏。
- **[仓库 +24MB]**：比切片方案多 10MB，换来许可解释零风险与 250→4 个文件的简化。
- **[生僻字]**：官方全字集，不做子集裁剪，不存在缺字回退。
- **[TTF 不做压缩]**：TTF 本身已是二进制表结构，gzip 收益有限；不额外增加压缩配置。

## Migration Plan

1. 资产目录替换为 3 个官方 TTF + 3 条 `@font-face` 的 CSS；`index.html` 的 link 路径不变。
2. `tokens.css` 两行（已完成）。
3. 跑 `npm run lint:styles`、`npx vue-tsc --noEmit`、`npm run build`（校验 `dist/fonts/harmonyos-sans/` 有 3 个 TTF、entry CSS 预算未超）。
4. 起服务 + Playwright 登录后核对计算字体与网络请求（应为 3 个本地 TTF）。

回退：删 `index.html` 的 link、还原 `tokens.css` 两行，立即回到雅黑；字体目录无代码引用，可整体删除。

## Open Questions

（无）
