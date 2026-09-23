## 1. 展示拆分（P0）

- [x] 1.1 助手消息拆成「回复」与「思考过程」两个带标题的独立区块（用户消息不变、消息顺序不变）。验证：3.1 断言两个标题出现在同一助手消息内。
- [x] 1.2 思考区块可折叠、默认展开、折叠态逐条独立；无思考过程时不渲染该区块。验证：3.1 三条断言（默认可见 / 收起后消失 / 无思考不渲染）。

## 2. 常量与样式

- [x] 2.1 三个标题文案进 constants.ts（回复 / 调用失败 / 思考过程），组件内无魔法字符串。验证：grep 组件内不出现这三个字面量。
- [x] 2.2 思考块与结果块视觉区分（虚线分隔 + 独立底色 + 保留换行），新增样式全部走令牌并写入 ModelDebugPage.style.css。验证：node tests/check-style-gates.mjs 四批通过。

## 3. 测试

- [x] 3.1 更新 frontend/tests/ai-assistant/p0/useModelDebug.spec.ts：两区块标题、思考默认展开→收起、无思考不渲染、失败标识为「调用失败」。验证：npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts 通过。

## 4. 门禁与复验

- [x] 4.1 前端门禁：npm run typecheck、npm run build、node tests/check-style-gates.mjs、npx vitest run tests/ai-assistant + /vue-frontend-check 三块报告。验证：全部通过、无新增告警。
- [x] 4.2 浏览器复验（真实后端 + 真实一次对话）：同一助手消息内可见两个标题；收起思考后正文消失且回复仍在；无控制台错误。验证：DOM 断言结果记录在交付说明里。
- [x] 4.3 零后端改动确认：git status 中 apps/ 与 engines/ 无本次新增改动；openspec validate distinguish-model-reply-and-thinking --strict 通过。验证：命令输出留档。
