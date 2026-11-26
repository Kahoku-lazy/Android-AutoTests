# HarmonyOS Sans SC · 本地网页字体

米哈游官网（`https://www.mihoyo.com/`）同款中文字体：平台 UI 文字统一用它渲染，替代原「微软雅黑」实际回退。

本目录放的是**华为官方发行包里的原始 TTF，未做任何改写**（不裁字形、不切片、不转码），以落在 `HarmonyOS Sans Fonts License Agreement` 的「unmodified copies」授权范围内。

## 版本与来源

| 项 | 值 |
|---|---|
| 字体 | HarmonyOS Sans SC |
| 版本 | Version 2.400（`name` 表 Version 2.400） |
| 文件 | `HarmonyOS_SansSC_Regular.ttf` / `_Semibold.ttf` / `_Bold.ttf` |
| 版权方 | Copyright 2021-2025 Huawei Device Co., Ltd. |
| 授权 | HarmonyOS Sans Fonts License Agreement（免费商用；见下方「许可条件」），全文见同目录 `LICENSE_Fonts` |
| 来源 | 华为官方发行包 `https://developer.huawei.com/images/download/next/HarmonyOS-Sans-v2.zip`（解压路径 `HarmonyOS Sans/HarmonyOS_SansSC/`） |

## 本目录结构

```
harmonyos-sans.css                  三档 @font-face（400 / 600 / 700）
HarmonyOS_SansSC_Regular.ttf        400 · 8.09MB
HarmonyOS_SansSC_Semibold.ttf       600 · 8.02MB
HarmonyOS_SansSC_Bold.ttf           700 · 7.99MB
LICENSE_Fonts                       华为 HarmonyOS Sans 字体许可原文
```

只带 400 / 600 / 700 三档：平台字重令牌里 500 与 800 的消费点极少（500 仅 5 处），由浏览器就近匹配到 400 / 700；现状微软雅黑同样没有 800 字面，观感不变。

## 使用方式

1. `frontend/index.html` 的 `<head>`：

   ```html
   <link rel="stylesheet" href="/fonts/harmonyos-sans/harmonyos-sans.css" />
   ```

2. `frontend/src/shared/styles/tokens.css`：

   ```css
   --font-body: "HarmonyOS Sans SC", "PingFang SC", "Noto Sans SC", "Microsoft YaHei", system-ui, sans-serif;
   ```

字体族名固定为 `HarmonyOS Sans SC`，与 CSS 内 `font-family` 一致；`--app-font` / `--el-font-family` 等别名自动继承。`@font-face` 里已显式声明 400/600/700，官方 Semibold 文件内部族名是 `HarmonyOS Sans SC Semibold`，不靠内部名匹配。

## 许可条件与合规

华为 `HarmonyOS Sans Fonts License Agreement` 的四条硬条件，以及本仓的对应做法：

| 协议条款 | 本仓做法 |
|---|---|
| ① 软件内须显著声明使用了 HarmonyOS Sans | 登录页页脚显示「字体 HarmonyOS Sans SC」（`views/LoginView.vue`） |
| ② 不得修改字体或其组件 | 直接使用官方原包 TTF，不裁字形、不切片、不转码 |
| ③ 不得把字体单独再分发/售卖；随软件分发可以 | 字体只随平台 `public/` 分发，未单独提供下载入口 |
| ④ 副本须保留版权声明与协议 | 字体内嵌版权字符串保留；`LICENSE_Fonts` 随目录入库、随 `dist` 发布 |

## 体积与加载

| 口径 | 大小 |
|---|---|
| 三档 TTF 合计 | 24.11MB（8.09 / 8.02 / 7.99） |
| CSS | 0.6KB（3 条 `@font-face`） |
| 首屏字体请求 | 页面用到的字重各一次：通常 400+600+700 三档全下（约 24MB），之后走浏览器缓存 |

平台是内网/本机使用，首屏一次 8–24MB 可接受；`font-display: swap` 保证字体未就绪时先显示回退字，不白屏。这份 CSS 与 TTF 是 `public/` 静态资产，不计入 `frontend/bundle-budgets.json` 的 `entry_css_kb`（那里只量 `dist/assets/*.css`），但评估首屏性能时要算进去。

## 升级

1. 从华为官方链接重新下载 `HarmonyOS-Sans-v2.zip` 并解压。
2. 用 `HarmonyOS Sans/HarmonyOS_SansSC/` 下的 `HarmonyOS_SansSC_{Regular,Semibold,Bold}.ttf` 整体替换本目录同名文件。
3. 校验：`name` 表 Version 与版权字符串；`fontTools` 读 `name` 表族名；`@font-face` 三档与文件一一对应。

## 为什么放 `public/` 而不是 `src/`

字体是静态资产，走 `public/` 由 Vite 原样拷贝到 `dist`，开发态与生产态同一路径 `/fonts/harmonyos-sans/…`，也不会被 Vite 重命名或内联。
