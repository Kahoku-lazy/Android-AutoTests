## Why

工作流任务弹窗改成 320px 左列后，设备下拉的文案 `192.168.35.57:39569 · SM-G9730 (ONLINE)` 放不下，选中值被截成 `… SM-G9730 (ON`。`(ONLINE)` 在下拉里是冗余信息：能进这个下拉的设备本来就按「可连地址」筛过一遍，在线是默认态。

## What Changes

- `deviceLabel()` 只在设备**不在线**时才附加状态后缀（如 `(OFFLINE)`、`(UNAUTHORIZED)`），在线设备只显示「可连地址 · 型号」。
- 同步改两处断言：`tests/shared/p0/device-address.spec.ts` 与 `tests/ai-assistant/p0/sop-run-form.spec.ts`。
- 设备地址取值口径（USB 序列号 / `IP:端口`）与不可选记录过滤**不变**。

## 关联文档

无独立需求编号。来源是本轮任务弹窗改版评审时留下的待定项（960px 两栏方案里的「设备标签会被截」），需求方确认按「去掉冗余 `(ONLINE)`」处理。

## Capabilities

### New Capabilities

无。纯展示文案调整，不改变任何需求级行为：`assistant-bound-sop` 与 `task-card-sop-form` 对设备下拉的要求是「展示可连地址（有型号时附带型号）」，从来没有要求状态后缀。

### Modified Capabilities

无。

## Impact

- 前端：`frontend/src/shared/helpers/device-address.ts`（`deviceLabel` 一个函数）。
- 测试：`frontend/tests/shared/p0/device-address.spec.ts`、`frontend/tests/ai-assistant/p0/sop-run-form.spec.ts`。
- 消费方只有工作流任务弹窗（`SopRunForm.vue` 的设备下拉）；设备管理表格用的是自己的列，不受影响。
