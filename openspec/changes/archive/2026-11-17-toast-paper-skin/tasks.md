# 任务：提示条纸片化

- [x] 1.1 `style.css`：`.el-message` 改纸面色 + 2.5px 墨边 + `3px 3px 0 0 var(--ink)` 硬影 + 等宽字体 + `--app-size-sm` 正文
- [x] 1.2 `style.css`：success / error / warning 图标映射到 `--app-status-success` / `--color-red-46` / `--c-ops`；关闭键次要色、hover 墨色
- [x] 1.3 `style.css`：新增 `.el-message__action`（按钮语义 + 波浪下划线链接外观 + focus outline）
- [x] 1.4 `helpers/sop-form.ts`：`sopSubmittedMessage()` 返回 `{ text, action }`
- [x] 1.5 `SopWorkflowSection.vue`：提示渲染成「只读正文 + 行动入口」两段，整条不再是一个按钮
- [x] 1.6 单测 `tests/ai-assistant/p0/sop-submit-link.spec.ts` 断言两段各自内容
- [x] 1.7 `.agents/skills/doodle-craft/references/components/feedback.md` §4 更新口径与反模式
- [x] 1.8 实跑 computed：底色 `rgb(243,239,226)`、`2px solid`（1.5px 取整后）、影 `rgb(30,30,36) 3px 3px 0`、圆角 `4px 8px`、等宽字体、动作 `underline wavy`
- [x] 1.9 `npx vitest run tests/ai-assistant` 12 文件 / 69 用例全绿；`npm run typecheck` 通过
