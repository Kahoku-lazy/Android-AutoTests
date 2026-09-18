## 1. 组件级动效令牌化

- [x] 1.1 全仓把 `transition` / `animation` 声明中的 `0.12s` / `.12s` 替换为 `var(--app-duration-fast)`（21 处）；验证：残留检索为 0
- [x] 1.2 `0.15s` / `.15s` → `var(--app-duration)`（11 处）；验证：残留检索为 0
- [x] 1.3 裸 `ease` → `var(--app-ease)`（14 处，与 CSS `ease` 严格同值）；`ease-in` / `ease-out` / `ease-in-out` / `linear` 保持不变；验证：`transition` 声明中不再出现裸 `ease` 关键字
- [x] 1.4 `0.1s` → `var(--app-duration-fast)`、`0.2s` → `var(--app-duration-slow)`；验证：残留检索仅剩 `1.4s` / `1.5s` 两处已登记例外
- [x] 1.5 删除替换产生的自引用兜底 `var(--app-duration, var(--app-duration))`（4 处，均在 `ToolboxPanel.style.css`）；验证：全仓检索该模式命中数为 0
- [x] 1.6 涉及 28 个文件的替换后逐项复核；验证：`npm run lint:styles` 退出码 0，`vite build` 通过

## 2. reduced-motion 降级补齐

- [x] 2.1 行级判定含 `transition: … transform …` 的文件（共 10 个，其中 7 个缺守卫）；验证：输出判定清单
- [x] 2.2 为 7 个缺守卫文件补 `@media (prefers-reduced-motion: reduce)` 块：`ToolboxPanel.style.css`（`.tb-chip/.tb-source/.tb-btn/.tb-card`）、`CaseBreakdown.vue`（`.case-group/.expand-icon`）、`ReportDetail.vue`（`.expand-icon`）、`TaskReport.vue`（`.case-expand-icon`）、`WorkflowFileBrowser.vue`（`.file-card`）、`AppSidebar.style.css`（`.sidebar__toggle/.sidebar-menu__item/.sidebar-menu__chevron`）、`style.css`（`.el-button:active` 的 `transform: none`）；验证：缺失数为 0
- [x] 2.3 确认 3 处无限装饰动画（`SkeletonCard` 1.4s、`TaskResultPanel` 1.5s、`KpiCard` 1.5s）已有降级块并被登记为例外；验证：三者均在守卫清单内

## 3. 门禁与验收

- [x] 3.1 `npm run lint:styles` 退出码 0；验证：批 1/2/3 全绿，别名 48 条与裸色字面量 33 处未上升
- [x] 3.2 `npx vite build --mode development` 通过（`built in 35.03s`，退出码 0）；验证：既有 `tests/dashboard/**` / `store.ts` / `ProjectTree.vue` 无关报错未新增
- [x] 3.3 降级块静态覆盖复核；验证：含 transform 过渡的文件缺守卫数为 0；编码完好（乱码扫描 0）
- [x] 3.4 Chromium 断言（真实 `tokens.css` + `style.css` + 两个模块的真实样式 + 复刻 DOM，共 **7 项全 PASS**）：`.tb-card` 计算时长为 `0.15s`（`--app-duration`）、`.file-card` 为 `0.12s`（`--app-duration-fast`）且缓动为 `cubic-bezier(0.25, 0.1, 0.25, 1)`（即 `--app-ease`）；`reducedMotion: reduce` 下两者计算时长均降为 `0s`。**限制**：契约级验证，未加载真实运行的应用与数据
- [x] 3.5 缓动口径澄清：未显式声明缓动的动效（如 `transition: transform var(--app-duration)`）沿用 CSS 初始值 `ease`，其曲线与 `--app-ease` **严格相同**，故合规；不强制为它们补写显式缓动（避免无意义的改动面）

## 4. 过程中自伤与恢复（必须如实登记）

- [x] 4.1 **事故**：补守卫时用了 PowerShell 5.1 的 `Get-Content -Raw`（默认 ANSI/GBK）读取 UTF-8 源文件，把中文读成乱码后以 UTF-8 写回，**损坏了 7 个文件**（`ToolboxPanel.style.css`、`CaseBreakdown.vue`、`ReportDetail.vue`、`TaskReport.vue`、`WorkflowFileBrowser.vue`、`AppSidebar.style.css`、`style.css`）；构建在 `CaseBreakdown.vue:167` 报 SFC 属性解析错误暴露了该问题
- [x] 4.2 **恢复**：先用"特有乱码字"扫描确认受损集合恰为这 7 个文件（tokenize 脚本用的是 .NET `File.ReadAllLines/WriteAllLines`，UTF-8 安全，未受损）；再 `git checkout --` 从 HEAD 恢复这 7 个文件；然后**用 UTF-8 安全的 `edit` 工具**重做它们的既有成果（`style.css` 的变更 1/4、`TaskReport.vue` 的变更 2 全部编辑），最后重做变更 12 的令牌化与守卫
- [x] 4.3 **验证恢复完整**：乱码扫描 0；`vite build` 通过（证明所有 SFC 可解析）；`lint:styles` 通过；`git diff --stat` 无整文件级 diff（行尾未被破坏）；7 项既有变更的浏览器断言按需复跑
- [x] 4.4 **流程修正**：后续所有涉及中文源码的批量改写一律改用 `edit` 工具，或在 PowerShell 中显式指定 `-Encoding UTF8` 与 `UTF8Encoding($false)`；脚本内的中文注释同样会因 .ps1 被按 ANSI 读取而失真，故脚本内容限于 ASCII