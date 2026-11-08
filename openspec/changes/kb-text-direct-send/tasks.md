## 1. 发送门控

- [x] 1.1 `helpers/mode.ts`：`canSendText(mode, connected, state)` 改为 `canSendText(mode, state)`——只在文字方式且没有回答进行中时为真，不再要求已连接；注释同步说明「未连接时发送会自动建连」。验证结果：`npm run typecheck` 通过。
- [x] 1.2 `useAssistantSession.ts`：`canType` 改为 `canSendText(mode.value, state.value)`。验证结果：`npx vitest run tests/knowledge-assistant` 30 条全绿（`text-chat.spec.ts` 已按新语义更新）。

## 2. 未连接时自动建连并补发

- [x] 2.1 `useAssistantSession.ts`：新增待发队列 `pendingTexts`；`submitText()` 在未连接时入队并 `void start(KB_MODE_TEXT)`，已连接时直接发送；`ready` 事件里 `flushPendingTexts()` 按顺序补发一次后清空；`cleanup()` 清空队列。验证结果：新增 `tests/knowledge-assistant/p0/text-direct-send.spec.ts` 7 条全绿，含「未连接发送 → 自动建连 → ready 后补发」「建连前连发两条按顺序补发」「空文本不建连」「语音方式不接收输入」「回答中不发」「建连失败不残留」。
- [x] 2.2 `index.vue`：`can-send` 由 `canType` 改为 `canType && canStart`（就绪检查留在页面层），占位文案固定为 `KB_TEXT_PLACEHOLDER`。验证结果：`npm run typecheck`、`vue-tsc` 通过；`socketOpen` 不再被页面引用，已从解构中移除。

## 3. 文案与按钮

- [x] 3.1 `constants.ts`：删除 `KB_TEXT_START_HINT`；`KB_STATUS_TEXT_TEXT.idle` 改为「输入问题即可开始」；`KB_TEXT_HINT` 与 `KB_EMPTY_HINT` 改成不暗示「先开始对话」。验证结果：`grep -rn "KB_TEXT_START_HINT" frontend/src` 无结果。
- [x] 3.2 `components/VoiceConsole.vue`：文字方式不渲染「开始对话」（`v-if="!isActive && isVoice"`），会话中仍显示「结束对话」。验证结果：`eslint` 与 `npx vitest run tests/knowledge-assistant` 通过。
- [x] 3.3 `frontend/src/modules/knowledge-assistant/AGENTS.md`：「会话方式」与「文字链路」两处同步为「文字直接输入发送、首次发送自动建连」。

## 4. 门禁

- [x] 4.1 `npx vitest run tests/knowledge-assistant tests/login` + `npm run typecheck` + `npm run build:check`。验证结果：知识库助手 30 条全绿；`vue-tsc --noEmit` 无输出；构建在门禁的 `vite-build` 项通过。
- [x] 4.2 `python run.py check`：验证结果 **22/23**，唯一失败为 `vitest`（既有 `LoginView.hero.spec.ts` 2 条，工作区登录页文案改动）；全量 vitest 493/495。
- [ ] 4.3 人工验证：文字方式不点任何按钮，直接在输入框回车 → 自动建连并出回答；语音方式仍要点语音键；文字服务未就绪时输入框保持禁用。**（待用户执行）**
