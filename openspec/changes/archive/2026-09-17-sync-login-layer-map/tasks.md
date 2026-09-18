## 1. 生成器：源码指纹 + 页头展示

- [x] 1.1 新增 `SOURCE_FILES`（登录模块 9 个）与 `OWN_FILES`（生成器 + 模板），合并为 `TRACKED`（11 个），并注明判据：「① 决定测量结果的源码 / ② 决定标注清单与呈现的生成器自身」
- [x] 1.2 实现 `fingerprint()`（逐文件 sha256 前 12 位）与 `digestOf()`（对指纹对象再取 sha256 前 12 位）。验证：多次运行摘要恒为 `7c205b9cc58d`
- [x] 1.3 生成时内嵌 `<script type="application/json" id="layer-map-provenance">`（JSON 中 `<` 转义为 `\\u003c` 防闭合），页头 meta 追加「源码指纹 7c205b9cc58d（覆盖 11 个受管文件）」。验证：产物内两处均命中，长度由 460045 → 454032 bytes（D 节文案切换 + 指纹）
- [x] 1.4 生成结束 stdout 增加 `digest` / `trackedFiles` / `syncHint`。验证：输出含 `"digest": "7c205b9cc58d"`、`"trackedFiles": 11`

## 2. 生成器：`--check` 模式

- [x] 2.1 在 `require('playwright')` **之前**拦截 `--check`，四种路径全部实测：已同步 exit 0；受管文件内容变更 exit 1 并点名；HTML 不存在 exit 1（提示重跑）；HTML 无指纹（旧版产物）exit 1（提示重跑）
- [x] 2.2 不依赖 dev server / 浏览器。验证：`--check` 分支在 `require(PW)` 之前 return，结构与耗时（约百毫秒级 vs 生成需数秒且必须连 5173）均可佐证；错误路径 A/B 亦在无渲染条件下正确判定

## 3. 规则登记

- [x] 3.1 `temps/login-layer-map/README.md`：新增「同步规则（改动登录页后必须重跑）」小节（受管清单表 + `--check` 三种结果 + 行号漂移边界）；目录表补 `--check` 说明
- [x] 3.2 `frontend/AGENTS.md`：新增「设计层地图产物（登录页）」小节，登记触发重跑的文件清单、两条命令、以及「`--check` 不覆盖行号漂移」的边界
- [x] 3.3 顺带修正 README 的失效描述：「关键结论」第 3 条原为**修复前**的缺陷记录（`.el-overlay` 424×403、引用 `LoginView.style.css:233` 这一已漂移行号），改为当前已修复状态（1440×900 = 视口、对照实验已一致、指向 `frontend-l5-overlay` 需求）

## 4. 验证与归档

- [x] 4.1 重新生成含 L5 修复后最新状态的 HTML，`--check` exit 0
- [x] 4.2 反向验证（源码漂移）：给 `LoginErrorOverlay.vue` 追加一行注释 → `--check` exit 1 且点名该文件；还原后 exit 0
- [x] 4.3 反向验证（生成器漂移）：给生成器追加一行注释 → `--check` exit 1 且点名 `login-layer-map.cjs`（证明 D2「生成器自身入指纹」生效）；还原后 exit 0
- [x] 4.4 渲染未回归：`verify-layer-map.cjs` 仍 26/6/4 个框徽标一一对应、`legendRows`=30、`leftoverDeadSelectors`=0、`errs`=[]；临时文件（`.bak`/`.hide`）已全部清理
