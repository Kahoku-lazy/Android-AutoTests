## 1. 页面重排（P0）

- [x] 1.1 把六个等权面板重排为三层：角色带 / 生效装配（工具 + Skill）/ 参考数据（知识库）+ 提示词折叠；对话移入右栏并排。验证：浏览器复查三层可辨、对话在未滚动时可见。
- [x] 1.2 角色带：页内分段入口（指向三个 role 路由）+ 模型名 / provider / 模态 / 连接态 + 工具·Skill·知识库计数。验证：4.1 用例 + 浏览器点分段项切换生效且面包屑不变。
- [x] 1.3 对话右栏常驻：消息区独立滚动（max-height + overflow-y auto），输入框与发送 / 清空常驻；空态给示例问法。验证：浏览器确认滚动只发生在消息区。

## 2. 分组与折叠（P1）

- [x] 2.1 工具按 category 分组，组头显示启用数与总数，条目保留只读/写与已启用/已停用徽标；组默认展开。验证：4.1 断言分组数与组头计数。
- [x] 2.2 提示词默认折叠，折叠头显示字数与库中当前值标识，展开才渲染 Markdown。验证：4.1 断言默认不渲染正文、点击后渲染。
- [x] 2.3 Skill 与知识库的组头带归属徽标（三模型共用 / 执行链路未挂载 RAG）。验证：4.1 断言两条文案出现在组头元素内。

## 3. 样式与拆分

- [x] 3.1 新增样式全部走令牌（--c-ai / --space-* / --app-size-* / --radius-*），写入 ModelDebugPage.style.css；无硬编码色值与字号。验证：node tests/check-style-gates.mjs 四批通过。
- [x] 3.2 若 ModelDebugPage.vue 超 500 行，抽 components/ModelDebugChat.vue（纯展示 + emits）。验证：两个文件行数均不超过 500。（实测 266 行，未触发抽取）

## 4. 测试

- [x] 4.1 更新 frontend/tests/ai-assistant/p0/useModelDebug.spec.ts：三层结构可见、工具分组与组头计数、提示词默认折叠与展开后渲染、两条归属标注在组头、角色分段项可点。验证：npx vitest run tests/ai-assistant/p0/useModelDebug.spec.ts 通过。

## 5. 门禁与复验

- [x] 5.1 前端门禁：npm run typecheck、npm run build、node tests/check-style-gates.mjs + /vue-frontend-check 三块报告。验证：全部通过、无新增告警。
- [x] 5.2 浏览器复验（真实后端）：三层可辨、执行模型工具分组计数正确、提示词默认折叠、对话未滚动即可见、分段切换生效；逐条对照方案 HTML 的 P0/P1。验证：DOM 断言结果记录在交付说明里。
- [x] 5.3 零后端改动确认：git status 中 apps/ 与 engines/ 无本次新增改动；openspec validate relayout-model-debug-page --strict 通过。验证：命令输出留档。
