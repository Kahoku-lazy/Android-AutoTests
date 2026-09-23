## 1. 章节头去掉重复 chip

- [x] 1.1 在 `frontend/src/modules/dashboard/index.vue` 的 `.ch-ai` `chip-row` 删除累计 Token、任务、费用三枚 chip，保留角色·累计 / 角色·今日

## 2. AI 用量卡隐藏「进入」

- [x] 2.1 在 `StatsCard.vue` 增加默认开启的展示开关（如 `showEnter`），为 false 时不向 `KpiCard` 传入非空 `enterLabel`，且有 `path` 时整卡仍 `clickable`
- [x] 2.2 `index.vue` 中 AI 用量五张 `StatsAppCard` 关闭「进入」；其它章节卡片不传该开关

## 3. 单测

- [x] 3.1 更新或补充 `frontend/tests/dashboard/p0/StatsCard.spec.ts`：默认有 path 仍有「进入」；`showEnter=false` 且有 path 时无按钮、点击整卡仍 `router.push`
- [x] 3.2 执行相关 vitest（至少 StatsCard p0）通过
