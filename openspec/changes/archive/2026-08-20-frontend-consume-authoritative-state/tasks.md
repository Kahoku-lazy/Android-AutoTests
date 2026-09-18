## 1. taskUtils 权威状态读取

- [x] 1.1 `deriveTaskStatus`/`isTaskQueued`/`taskBucket` 改读 `task.state`（回退 idle），删除三元组判定分支与漂移补丁；验证 `npx vue-tsc --noEmit` 相关错误归零（分步跑）

## 2. 本地镜像同步（grep `\.running\s*=` 逐一核对补齐）

- [x] 2.1 `index.vue`：启动对象/队列激活对象加 `state:"running"`；排队加 `state:"queued"`；失败/取消加 `state:"idle"`；停止加 `state:"done"`；新任务创建 ×2 加 `state:"idle"`；`loadTasks` 映射加 `state`
- [x] 2.2 `useTaskOperations.ts` 同 2.1 五类点补 state
- [x] 2.3 `useTaskWebSocket.ts`：run_finished/device_error 加 `state:"done"`
- [x] 2.4 `TaskDetail.vue`：停止加 `state:"done"`；队列激活加 `state:"running"`；取消加 `state:"idle"`；重启新任务对象加 `state:"idle"`

## 3. report-generator 小写口径

- [x] 3.1 `api.ts` STATUS_LABEL_MAP/statusBadgeClass 改小写键（删大写列）
- [x] 3.2 `constants.ts` STATUS_KEYS 值/LABELS 键/徽章映射改小写
- [x] 3.3 `index.vue` 筛选 tabs key 改小写；`TaskReport.vue` 状态映射与徽章判断改小写

## 4. 门禁与文档同步

- [x] 4.1 前端门禁：`npm run typecheck` 全量含既有 spec 类型债（24 行，均非本变更引入——涉及 `mockResolvedValue`/字面量缺字段，与 state 无关；vitest 行为测试兜底）+ `npm run build` 全过；test-runner vitest **76/76 全过**（taskUtils.spec 已按权威 state 语义显式更新）
- [x] 4.2 后端回归：`python -m pytest -m "unit or integration" --nomigrations -q` **308 passed**（前端变更不触后端）
- [x] 4.3 Checklist §五 P2 权威状态行补「前端侧完成」；L4 详档 §六 收敛项 4/5 标注已落地
