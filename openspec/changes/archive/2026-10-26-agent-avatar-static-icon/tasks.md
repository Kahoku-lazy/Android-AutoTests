## 1. 图标资源与常量

- [x] 1.1 新增 `frontend/public/agent-avatar.svg`（128 网格、透明底、内置机器人头像），用浏览器直接打开该文件确认渲染正确
- [x] 1.2 `frontend/src/modules/ai-assistant/constants.ts` 增加 `AGENT_AVATAR_SRC = "/agent-avatar.svg"`，删除 `DATA_IMAGE_PREFIX` 与 `isImageAvatar`；用 `rg "isImageAvatar|DATA_IMAGE_PREFIX" frontend/src` 确认无残留引用

## 2. 看板线路卡

- [x] 2.1 `components/AgentRouteCard.vue`：头像改为固定 `<img :src="AGENT_AVATAR_SRC">`，删除 `agentAvatar` prop 与 emoji/图片分支，样式去掉 3px 墨色边框与暖色底；验证：`npx vue-tsc --noEmit` 无 prop 类型报错
- [x] 2.2 `index.vue` 与 `helpers/assistant-cards.ts`：`AssistantCard` 去掉 `avatar` 字段、模板去掉 `:agent-avatar`；验证：`rg "agentAvatar" frontend/src` 无命中
- [x] 2.3 更新 `frontend/tests/ai-assistant/p0/AgentRouteCard.spec.ts`：断言头像容器内是固定图标且与传入数据无关；验证：`npx vitest run tests/ai-assistant` 通过

## 3. 配置页

- [x] 3.1 `components/AgentBasicInfo.vue`：「头像」项改为只读预览（64px 内置图标）+「系统内置头像，不可修改」，删除上传按钮、文件选择器触发与输入框；验证：页面上 `rg "上传图片|Emoji 或留空"` 无命中
- [x] 3.2 `AgentDetail.vue`：删除 `uploading` / `fileInput` / `triggerUpload` / `handleAvatarUpload` 与隐藏 `<input type="file">`；`form` 去掉 `avatar`，保存 payload 不再带 `avatar`；验证：`rg "uploadAvatar|fileInput|reader" frontend/src/modules/ai-assistant` 无命中
- [x] 3.3 `api/agents.ts` 删除 `uploadAvatar`；验证：`rg "upload-avatar" frontend/src` 无命中

## 4. 后端与契约

- [x] 4.1 `backend/apps/ai_assistant/urls.py` 去掉 `UploadAvatarAPIView` 的 import 与 `upload-avatar/` 路由，删除 `backend/apps/ai_assistant/views_upload_drf.py`；验证：`POST /api/ai/upload-avatar/` 返回 404
- [x] 4.2 `openspec/openapi.yaml` 删除 `/api/ai/upload-avatar/` 路径；验证：`openspec validate --all` 通过

## 5. 门禁与回归

- [ ] 5.1 `cd frontend && npx vue-tsc --noEmit && npm run lint:styles` 通过 —— `vue-tsc` 已通过；`lint:styles` 报 40 条 G6 违规，全部位于 `modules/task-list/**`（HEAD 上已存在，本次未触碰该模块），与本次变更无关
- [ ] 5.2 仓库根跑 `python run.py check` 通过（与 CI 同一批检查）—— 阻塞项 21/22 通过；唯一失败的 `openapi-schema` 由工作区里他人未提交的 5 处 `/api/auth/*` 描述改动引起（重新生成后与基线只在这 5 行描述上不同，上传头像路径两边都不存在），与本次变更无关
- [ ] 5.3 人工核对：`/ai-assistant/agents` 312px 卡片头像与三行等高、`/ai-assistant/agent/:id` 头像只读且无上传入口、配置保存后卡片外观不变 —— 未做，需要起服务并登录；已用 Chrome 直接打开 `public/agent-avatar.svg` 确认图标本身渲染正确
