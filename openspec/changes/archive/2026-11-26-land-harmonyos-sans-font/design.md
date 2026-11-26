# Design: land-harmonyos-sans-font

## Context

- 归档单 `2026-11-25-switch-ui-font-to-harmonyos-sans` 的代码从未进主干：`tokens.css` 仍是雅黑链、
  `index.html` 仍连 Google Fonts、`frontend-l0-design-tokens` 无字体要求
- 需求方 2026-11-26 裁决：字体二进制**不入库**，本地缺失自动取用，不进 PR
- 官方发行包 `https://developer.huawei.com/images/download/next/HarmonyOS-Sans-v2.zip` 实测 HTTP 200、
  `Content-Length: 61,682,784`；解压路径 `HarmonyOS Sans/HarmonyOS_SansSC/HarmonyOS_SansSC_{Regular,Semibold,Bold}.ttf`
- `#76` 已把 `frontend/public/fonts/harmonyos-sans/*.ttf` 写进 `.gitignore`，并已按「含 24.1MB 字体」重标定 `tests/perf` 传输预算
- CI 的 frontend job 走 `utils/check_gates.py` 的 `vite-build`，执行 `npx vite build`，**不经过 npm 生命周期钩子**

## Goals / Non-Goals

**Goals**

- 主干上字体真的换成鸿蒙，且断网可用（文件本地、无第三方域名）
- 全新克隆后一条命令即可补齐字体；忘记补也不会静默坏掉
- 不让 CI 为 59MB 下载买单

**Non-Goals**

- 不做字体子集化 / woff2 / 裁剪（需求方明确排除，且与归档单的 MUST 冲突）
- 不改字号、字重、行高、间距刻度
- 不在 CI 里跑字体下载或字体一致性断言

## Decisions

### D1 资产只入库文本三件 + 品牌字 woff2

`harmonyos-sans.css`（3 条 `@font-face`）、`README.md`（版本 / 来源 / 许可）、`LICENSE_Fonts`（华为协议）入库；
三个 TTF 被 `.gitignore` 排除。品牌手写体 `ziku-feiyang.woff2`（795KB）入库——它体积小、来源单机无二份，
且 `ziku-feiyang.ttf` 本来就在库里（main 已跟踪 1.4MB），woff2 只是让首屏少下 600KB。

### D2 取用脚本独立成 `utils/fetch_fonts.py`，不走构建期副作用

不在 `vite.config.js` 里做副作用（构建配置不该联网）。脚本自己负责：缓存发行包到 `temps/cache/`、
按文件名解出三档到目标目录、按体积（≥8MB）校验、幂等（已就位直接返回 0）。

### D3 三个触发点，全部「软失败」

| 触发点 | 为什么 | 行为 |
|---|---|---|
| `package.json` 的 `predev` / `prebuild` | 开发者最常用的两个入口 | `--soft`，取不到只警告 |
| `utils/service_ctl` 的 frontend `preflight` | `python -m run start frontend` 直接 `npx vite --host`，绕过 npm 钩子 | 同上 |
| 手动 `python -m utils.fetch_fonts` | 排障与 CI 以外的显式场景 | 不带 `--soft`，失败返回 1 |

### D4 CI 不取字体

字体不进 JS/CSS 包，构建不需要它们；e2e / perf 需要时由本机先取。CI 若下载 59MB，等于给每次 PR 加一份无收益的耗时。

### D5 规格写「不入库」而不是只写「本地分发」

归档单的 MUST 只说「取官方原版 TTF、不依赖 CDN」，没说这些文件从哪来。若不补一条，后来者会按「资产入库」理解，
与本次裁决打架。因此 delta 里明确：二进制 MUST NOT 入库、缺失 MUST 能按需取用、取用失败 MUST NOT 阻断构建。

## Risks / Trade-offs

- [全新克隆首屏是雅黑] → 属预期：取用脚本与 README 都写明一条命令；`tests/perf` 因字体缺失 skip，不会假绿
- [华为官方包地址变更] → 失败提示里带完整 URL 与解压路径，可手工放置；脚本按体积校验而不是按内容哈希，能容忍包内其它文件变化
- [首次下载 59MB 拖慢开发] → 只在缺失时发生；缓存在 `temps/cache/`（已忽略），二次不重复下载
- [`.gitignore` 规则依赖 `#76`] → 该规则已在主干；本单再核一次，若被后来者删掉会出现「误入库 24MB」

## Migration Plan

1. 落字体接线与资产（样式表 / README / 协议 / ziku woff2）
2. 落取用脚本与三处触发点
3. 落规格 delta 与技能口径

**Rollback**：还原 `tokens.css` 三行、`index.html` 链接、`style.css` 品牌字声明；删 `utils/fetch_fonts.py` 与两处 hook 调用。
