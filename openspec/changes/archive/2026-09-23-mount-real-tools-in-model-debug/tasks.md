## 1. 后端：真实装配 + 设备校验

- [x] 1.1 把候选设备口径（`devices:available` 的来源常量与解析函数）从 views_tool_debug_drf.py 上移到 tools.py，视图改为调用同一函数。验证：`python manage.py check` + 平台工具调试页 schema 的 options 行为不变（相关单测通过）。
- [x] 1.2 `build_debug_role` 按角色真实工具子集装配（不空工具集），Skill 仍不挂。验证：新增单测断言三角色调试角色的工具名等于各自 RoleSpec 子集、skill_dirs 为空。
- [x] 1.3 `run_role_chat` 接收并校验 serial（可见 + 在线 + 未占用），按「工具签名是否含 serial」决定是否必填；serial 以 `当前设备 serial：{serial}` 注入模型输入；返回值透出 `tool_usage`。验证：新增单测（缺 serial 4xx、不可用 serial 4xx 且未调用模型、合法 serial 进入输入、tool_usage 透出、规划角色可不带 serial）。
- [x] 1.4 视图 `POST /api/ai/model-debug/<role>/chat/` 透传 `serial`。验证：契约单测断言 400 可读错误与 200 返回字段含 tool_usage。

## 2. 前端：设备选定 + 授权确认 + 去超时 + 轨迹

- [x] 2.1 页内新增设备下拉：候选取 `/devices/` 中状态 ONLINE 且 `occupied_by` 为空者；角色需要设备时必选（未选则发送按钮不可用并提示）。验证：单测断言候选过滤与未选时的禁用/提示。
- [x] 2.2 发送前二次确认（ElMessageBox，中文按钮）：列出目标设备与写工具数量；取消不发请求、确认才发。验证：单测断言确认文案含设备与写工具数、取消路径不调用 chat。
- [x] 2.3 去掉固定 5 分钟上限与相关文案：请求不再带 timeout；页面提示改为如实描述（挂载真实工具 / 会真实操作所选设备）。验证：grep 不再出现 300_000 与「最长 5 分钟」；单测断言新文案。
- [x] 2.4 助手消息新增「工具调用」轨迹区块（工具名 + 只读/写徽标 + 结果状态 + 次数），样式全走令牌写入 ModelDebugPage.style.css。验证：单测断言轨迹条数与徽标、`node tests/check-style-gates.mjs` 四批通过。

## 3. 门禁与复验

- [x] 3.1 后端门禁：`python manage.py check`、`ruff check`、`makemigrations --check`、`pytest tests/graybox/unit`。验证：全绿（408 passed）。
- [x] 3.2 前端门禁：`npm run typecheck`、`npm run build`、`node tests/check-style-gates.mjs`、`npx vitest run tests/ai-assistant` + /vue-frontend-check 三块报告。验证：全绿（81 passed）、无新增告警。
- [x] 3.3 真实复验（浏览器 + 真机 R5CT62RH88F）：确认框出现且列出设备与写工具数；发送后助手消息内可见工具调用轨迹；设备侧确实发生对应操作。验证：DOM 断言 + 设备侧观察记录写进交付说明。
- [x] 3.4 零越界确认：`python tools/gen_arch_stats.py --check-boundaries` 无违规；`openspec validate mount-real-tools-in-model-debug --strict` 通过；git status 中 engines/ 无本次新增改动。验证：命令输出留档。
