## 1. doodle-craft 消费方列举

- [x] 1.1 `SKILL.md` 选型表行「资源入口卡（用例 / 元素 / 页面流）」改为「资源入口卡（用例）」。验证：该行 grep「元素 / 页面流」命中 0。**验证结果**：已改，三文件模块引用扫描 0 命中
- [x] 1.2 `references/components/cards.md` SketchCard「用途：用例 / 元素 / 页面流资源网格入口」改为「用途：用例资源网格入口」。验证：该行 grep「元素 / 页面流」命中 0。**验证结果**：已改

## 2. frontend-change-plan 原型模板

- [x] 2.1 删页面流模块深度表行（`<tr>…页面流…</tr>`）；版式 C「用例工作台、页面流画布台」→「用例工作台」；版式 H「用例、页面流共用」→「用例」；P2 行删「页面流列表 + 画布外框；」；导航①「元素/用例/页面流用」→「用例用」；matrix lead 删「页面流走「Hub→画布」；」。验证：上述各句 grep 页面流/元素 命中 0。**验证结果**：原子脚本逐处替换（每处断言唯一命中），全部完成
- [x] 2.2 删「页面流 · Hub → 画布」迷你原型段（`<h2>` + `div.wb[data-accent=workflow]` 整块）与脚本 `/* Workflow */` 块（enterWf/backWf + 4 个 wf-* 监听）；`PAGES.matrix` 改「报告 / 用例」。验证：模板 grep `页面流|page_flow|wf-|Workflow` 命中 0，无悬空 getElementById 引用。**验证结果**：leftover module refs []，getElementById wf refs []
- [x] 2.3 模板结构自检：浏览器/解析确认无残留 wf-* id 引用、页面切换脚本不因缺元素报错。验证：grep `getElementById("wf-` 命中 0。**验证结果**：0 命中；page-matrix section 与 PAGES 键（plan/nav/hub/ai/matrix）保留，导航切换不受影响；通用版式规则与 CSS 调色板保留

## 3. 收口

- [x] 3.1 残留扫描 `.agents/skills` 全目录 `页面流|page_flow|modules/workflow` 命中 0；逐文件暂存（SKILL.md 用 HEAD+本单版部分暂存避开并行 hunk），提交 `docs(skills): 清理技能文档中已退役的页面流/元素定位举例` 并推送 Kahoku。验证：`git show --stat` 仅含 3 个技能文件 + 本变更目录；推送成功。**验证结果**：三文件模块引用 0；提交见 git log