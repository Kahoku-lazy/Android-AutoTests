## 1. 删除三处被替代的代码

- [x] 1.1 `StructureAnalysisPanel.css`：删 `.sap-label-hit` 本体与 `td:has(.sap-label-hit)` 定位基准规则（含其注释）；**保留**紧邻的 `td:has(.sap-thumb-cell)` 规则。验证：`Select-String -Pattern 'sap-label-hit'` 在全仓命中 **0**；`npm run lint:styles` 五批全过
- [x] 1.2 `tokens.css`：删 `--insp-pad-filter`、`--insp-pad-hint`、`--insp-hint-gap` 三个零引用令牌及其注释，并把 `--insp-gap-row` 上方「工具条 / 筛选栏 / 分页栏」改为「工具条 / 分页栏 / 快照抽屉」。验证：三令牌全仓命中 **0**；扫描器复测该文件「声明 12 → 9 个，零引用 3 → 0 个」
- [x] 1.3 `ScreenshotView.vue`：删 `visibleRectCalls` 的 ref 声明与注释、`rectCalls` 计数（声明 + 两处 `+= 2`）、`defineExpose(...)` 与「自检钩子」注释。验证：`visibleRectCalls\|rectCalls` 全仓命中 **0**；`npx vue-tsc --noEmit` 无新增错误

## 2. 门禁与验收

- [x] 2.1 前端门禁：`npm run lint:styles`（批 1 / 1b / 2 / 3 / 4 全过，裸色字面量存量清单 **32 处未上升**）、`npx eslint src/modules/device-inspector`（0 error / 1 条既有空块 warn）、`npx vue-tsc --noEmit`（**恰为 3 条既有 `ProjectTree.vue`**）、`npx vite build`（✓ built in 3m39s）。`npx vitest run` 见下「偏差」
- [x] 2.2 真浏览器冒烟（Playwright，`temps/probe_inspector_smoke.py`）：登录 → `/inspector` → 开抽屉。验证：**console error = 0**；面板渲染 1 个、分组筹码 5 个（布局容器 / 滚动·集合容器 / 内容控件·文本 / 图标 / 其它）、表头 15 列与 `COLUMN_SPECS` 一致、分页「第 1 / 1 页 · 共 0 条」、空态文案在位；抽屉打开且清空键仍是上一单的硬边皮肤（`radius 2px`、灰底 `rgb(201,202,204)`）；**DOM 里 `.sap-label-hit` 命中 0 个元素**（直接证明删掉的 CSS 永不匹配）；截图 `temps/probe-smoke-after.png`
- [x] 2.3 反向复核：重跑三个扫描脚本。验证：`sap-label-hit` 从 CSS 类清单与「未出现」清单中消失（scan4 的 `模板里出现过但 CSS 未定义` 变为 `[]`）、三令牌消失、`visibleRectCalls` 消失，且**未新增**任何零引用项

## 3. 归档

- [x] 3.1 `npx openspec validate purge-inspector-superseded-leftovers --strict` 通过；`npx openspec archive purge-inspector-superseded-leftovers -y` 成功；`npx openspec validate --specs --strict` 保持 55 passed / 0 failed
- [x] 3.2 归档留痕（见 §4）

## 4. 验收留痕与偏差（apply 期实测）

- **删除面**：3 个文件 8 处替换，**净减 17 行**（`StructureAnalysisPanel.css` −5、`tokens.css` −4、`ScreenshotView.vue` −8）。无新增/删除测试文件。
  - 更正：归档时初稿写「净减 34 行」是按行块估算的笔误，apply 后逐处复核为 17 行，已按实测改正。另注：`ScreenshotView.vue` 的 `git diff --stat`（229+/118−）包含本会话其它变更，不能用来度量本单。
- **vitest 的偏差（如实记录，未归因于本变更）**：`npx vitest run` 报 **49 个文件 / 253 个用例全部通过、0 失败**，但同时有 **1 条 unhandled error** —— 现场证据是 `[vitest-pool]: Timeout terminating forks worker for test files …`（`TaskAttemptCard.spec.ts` / `useCaseSheet.spec.ts` / `api.spec.ts` 等）与一段 timer 栈。与加载前一次运行（50 文件 / 256 用例）的差异**来自这一条 worker 拆卸超时**，而非用例失败：
  - 本条变更的爆炸半径 `tests/device-inspector` 单独跑 → **4 文件 / 20 用例全过**；
  - 被点名的 `TaskAttemptCard.spec.ts` 单独跑 → **4/4 全过**；
  - 磁盘上有 **51 个 spec 文件**，其中若干是并发会话刚新增（`??` / `A` 状态，如 `ToolDebugPage-device-options.spec.ts`、`toolbox-assembly-prompts.spec.ts`、`useToolDebug.spec.ts`、`token-storage.spec.ts`），另有并发会话删除的 `useAuthPool.spec.ts` —— **测试清单在本次校验期间被并发会话改动**，故「50 文件 / 256 用例」不是稳定基线。
  - **未能坐实**具体哪两个文件未产出结果：我尝试用 `--reporter=json`/`--reporter=basic` 捕获机器可读清单时，后者在 vitest v4 上不是合法 reporter（启动报错 `Failed to load custom Reporter from basic`），已放弃再做一轮完整复跑；上述判断依据是「所有产出的文件全过 + 单独复跑全过 + 拆卸超时日志」三条。
- **本机负载**：`vite build` 由加载前的 1m22s 变为 3m39s、`vitest` 由 195s 变为 320s，说明校验期间机器负载显著升高（并发会话在跑自己的门禁）——这是上述超时最可能的外部原因。
- **未新增守门**：本次**没有**为「模块令牌必须被引用」加门禁（设计 D4 已说明理由与代价：会立刻扫出 `ai-assistant` 19 + `workflow` 20 处既有死令牌），仍在 design 的 Open Questions 里待你决定。
