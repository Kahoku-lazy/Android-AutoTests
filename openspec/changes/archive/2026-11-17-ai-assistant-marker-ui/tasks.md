## 1. 样式骨架与令牌

- [x] 1.1 `tokens.css` 只保留 5 支笔色原子；浅底 / 渐变改由组件用 `color-mix` 从 `--assistant-marker` 派生。验证：`node tests/check-style-gates.mjs` 悬空引用仍为 21 处（与改动前同，全部在 `task-list`），未新增。
- [x] 1.2 新增 `helpers/marker.ts`（笔色 → 行内 `--assistant-marker`）与 `helpers/editor-form.ts`（空白表单 / 由名片预填 / 提交载荷）。验证：`tests/ai-assistant/p0/editor-form.spec.ts` 覆盖载荷形状与未知笔色回落。

## 2. 助手卡片

- [x] 2.1 `AssistantCard.vue`：纸底 + `2.5px dashed` 墨框 + 笔色 `4px 4px 0` 硬影 + 三档微倾，hover 回正抬起；`prefers-reduced-motion` 降级。验证：`node tests/check-dashed-whitelist.mjs` 通过（非白名单文件 0 处虚线）。
- [x] 2.2 卡片三样信息：名称 16px 重字重、中间 88px 头像或笔色深到浅圆（无字）、配置名 14px 次级色；两个动作改成 30px 手绘小按钮带键盘焦点环。验证：P0 用例仍断言 `.assistant-card__swatch` 与三段文案。

## 3. 配置弹窗

- [x] 3.1 `api/assistants.ts` 增加 `updateAssistant`（`PATCH` + multipart，支持 `clear_avatar`）。验证：`npx vue-tsc --noEmit` 通过。
- [x] 3.2 `index.vue` 用 `el-dialog` 承载 `AssistantEditor`；「新建助手」打开空表单，「配置」打开预填表单。验证：真浏览器点「配置」后名称与 Agent 配置均回填（`temps/ai_assistant_marker_probe.py`）。
- [x] 3.3 `AssistantEditor.vue`：头像（预览 + 选择 + 移除，置于最上方）/ 名称 / Agent 配置 / 工具域 / 预设，实线墨框控件与 `DoodleBtn` 动作；空工具可提交，接口报错就地展示。验证：P0 覆盖字段顺序与「不选工具也能提交」「接口拒绝时展示错误」。

## 4. 对话页

- [x] 4.1 `openChat` 带 `name`；页头只留助手名与图标，「‹ 返回助手」移到 `.doc-body` 顶部工具条；缺失名时回落「对话」。验证：真浏览器页头无按钮、正文左上可返回。
- [x] 4.2 左栏多对话：抽出 `components/AssistantLanePanel.vue` —— 纸色虚线卡（1.5px 浅墨、四边闭合、不倾斜）+ 名称「对话栏」+ 笔色与模块色双波浪线 + 拉满整列高度的纵向虚线分隔（落在两栏间距中线，与面板右边框留 12px）；当前栏浅蓝填充；每栏显示标题与状态（含 `done`→已完成）。验证：`.lane-panel__lane.is-current` 落在被点栏，虚线门禁 OWNERS 同步登记新组件。
- [x] 4.3 消息流：助手气泡笔色描边、用户气泡纸色 + 墨色描边、发送钮笔色深到浅渐变；空态、进行中状态行与取消。验证：P0「刷新后轮询到进行中的结果」通过。

## 5. 对话栏重命名与删除

- [x] 5.1 后端服务：`rename_thread`（空标题落 `""`、按 80 截断）与 `delete_thread`；`finish_message` 先查栏是否还在，避免后台线程写已删行。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant/api/test_assistant_threads.py -q`。
- [x] 5.2 接口：`PATCH .../threads/{thread_id}/` 改名、`POST .../threads/{thread_id}/delete/` 删除记录（`DELETE` 仍是取消）。验证：同文件覆盖 200 / 空标题 / 404 / 级联删消息。
- [x] 5.3 前端：`api/assistants.ts` 加 `renameThread` / `deleteThread`；面板行内 `✎` 就地改名（Enter 提交、Esc 取消、失焦提交）与 `✕` 删除（`ElMessageBox` 二次确认，删当前栏后自动切栏或新建）。验证：`tests/ai-assistant/p0/assistant-lane-panel.spec.ts`。
- [x] 5.4 配色：当前栏改浅蓝填充（`--c-workflow 40%` + 白）+ 2px 墨框；「新建对话」换 `DoodleBtn tone="teal"`。验证：真浏览器取计算样式为 `rgb(78,205,196)` 与浅蓝底。

## 6. 规格登记

- [x] 5.1 扩写 `.agents/skills/doodle-craft/references/components/assistant-marker-card.md`：色板 / 卡片 / 配置弹窗 / 对话页 / 反模式。
- [x] 5.2 `SKILL.md` 组件目录补「AI 助手（专有）」一行，线型规则表的助手颜料片一行补上卡内动作按钮。验证：OWNERS 未放宽。

## 7. 关单

- [x] 6.1 `npx vue-tsc --noEmit`、`npx vitest run tests/ai-assistant`（7 条）、`node tests/check-dashed-whitelist.mjs` 通过；`node tests/check-style-gates.mjs` 未新增悬空引用（存量 21 处属 `task-list`，本变更未触碰）。
- [x] 6.2 真浏览器截图三处界面并走通「新建 → 配置改名 → 卡片同步 → 清理」：`temps/ai-assistant-cards.png`、`temps/ai-assistant-config.png`、`temps/ai-assistant-chat.png`、`temps/ai-assistant-cards-2.png`。
