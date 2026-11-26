## ADDED Requirements

### Requirement: 全站 UI 字体由本地官方原版 HarmonyOS Sans SC 承载

全站 UI 文字（`--font-body`，以及由它派生的 `--app-font` / `--app-font-display` / `--el-font-family`）MUST 首选 `HarmonyOS Sans SC`，其字体文件 MUST 取华为官方发行包中的**原始 TTF**（`HarmonyOS_SansSC_Regular/Semibold/Bold.ttf`），MUST NOT 做字形裁剪、unicode-range 切片或格式转码，MUST NOT 依赖第三方字体 CDN 或外部域名。字体族 MUST 覆盖 Regular（400）、Semibold（600）、Bold（700）三档；请求 500 与 800 字重时 MAY 由浏览器就近匹配到 400 与 700，MUST NOT 为此新增字重令牌。字号 7 档刻度、字重 5 档令牌、行高与间距 MUST NOT 因换字体而改变。品牌手写体 `Ziku FeiYang` MUST 继续作为 `--font-brand` 的首选族。

#### Scenario: 页面文字由本地鸿蒙字体渲染

- **WHEN** 打开任一平台页面（登录页、看板、知识库等）并读取 `body` / `.wb-shell` 的计算 `font-family`
- **THEN** 首族为 `HarmonyOS Sans SC`
- **AND** 浏览器加载的字形来自 `/fonts/harmonyos-sans/` 下的官方 TTF，请求列表中不出现第三方字体域名

#### Scenario: 字体文件保持官方原样

- **WHEN** 检查字体取用后的 `frontend/public/fonts/harmonyos-sans/`
- **THEN** 三个文件是华为官方发行包中的原始 TTF（`name` 表 Version 2.400、版权 Huawei Device Co., Ltd.），文件数等于 `@font-face` 条数（3）
- **AND** 不存在 woff2 分片、子集化产物或改名文件

#### Scenario: 断网或阻断外域时字体不退化

- **WHEN** 在禁止访问外部域名的浏览器上下文里打开页面
- **THEN** 计算 `font-family` 与联网时一致，文字仍以鸿蒙字体渲染（文件已在本地）
- **AND** 字体文件缺失时整链回退到 PingFang SC / Microsoft YaHei，页面不报错

#### Scenario: 品牌字仍是手写体

- **WHEN** 检查侧栏品牌名、页头标题与登录页 Hero 标题的计算 `font-family`
- **THEN** 首族仍为 `Ziku FeiYang`
- **AND** 其回退链在 `Ziku FeiYang` 缺字时落到 `HarmonyOS Sans SC`

#### Scenario: 刻度与体积预算不因换字体改变

- **WHEN** 运行 `npm run lint:styles` 与 `npm run build`
- **THEN** 字号 7 档与字重 5 档声明与换字体前逐一相同，几何尺度门禁无新增命中
- **AND** `@font-face` 声明不出现在 entry CSS 中（`index.html` 外链独立样式表），entry CSS 仍在 `bundle-budgets.json` 预算内

### Requirement: 字体二进制不入库，缺失时按需取用且不阻断构建

字体二进制（三个 TTF，合计约 24.1MB）MUST NOT 入库；仓库只跟踪 `@font-face` 样式表、来源说明与字体协议。缺失时 MUST 能由 `python -m utils.fetch_fonts` 按需取用（幂等：已就位即跳过）。`npm run dev`、`npm run build` 与 `python -m run start frontend` MUST 在启动前尝试取用，但取用失败 MUST NOT 阻断构建或启动，此时 MUST 回退到系统字体且 MUST NOT 报错；CI 构建 MUST NOT 为此下载字体。

#### Scenario: 字体二进制不入库

- **WHEN** 在全新克隆的仓库里执行 `git ls-files frontend/public/fonts/harmonyos-sans`
- **THEN** 只列出 `harmonyos-sans.css` / `README.md` / `LICENSE_Fonts`，不出现任何 `.ttf`
- **AND** `.gitignore` 命中 `frontend/public/fonts/harmonyos-sans/*.ttf`

#### Scenario: 缺失时按需取用且不阻断构建

- **WHEN** 字体尚未就位时执行 `npm run build` 或 `python -m run start frontend`
- **THEN** 先尝试 `python -m utils.fetch_fonts`（已就位则秒过），取用失败只打印可操作提示
- **AND** 构建与启动仍然成功，页面回退到系统字体，`tests/perf` 因字体缺失 skip 而不是判通过
