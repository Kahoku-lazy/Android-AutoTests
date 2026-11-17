## Context

见 `proposal.md` 的 Why。`deviceLabel(device)` 是设备下拉的文案生成器，位于 `shared/helpers/device-address.ts`，当前实现无条件把 `status` 拼成 `(ONLINE)` 后缀。消费方只有工作流任务弹窗；设备管理页的表格列由 `DeviceIdentityCell` 自己渲染，不走这个函数。

## Goals / Non-Goals

**Goals:**

- 在线设备的下拉文案收短到「可连地址 · 型号」，320px 左列放得下。
- 不在线设备仍然一眼可辨（保留非在线后缀）。

**Non-Goals:**

- 不改设备地址取值口径（USB 序列号 / `IP:端口` / 别名过滤）。
- 不改设备管理页的表格与卡片。
- 不在本次引入「下拉只列在线设备」的过滤（那是行为变更，需另立需求）。

## Decisions

1. **只对非在线状态拼后缀。** 判据是 `status !== "ONLINE"`，而不是「不拼状态」：离线、未授权等状态仍要能看见，否则用户在弹窗里看不出这台机器当前不可用。备选是彻底删掉状态：会丢掉离线信号，不采纳。
2. **改共享函数，不在弹窗里另拼文案。** 消费方只有一个，但口径应只留一处；在 `SopRunForm.vue` 里拼标签会让「地址取哪个」与「标签怎么写」分家。备选是新增 `deviceLabelShort()`：多一个近似函数，容易被误用。
3. **状态大小写保持原样。** 后端给的是大写枚举值，函数不做格式化，避免与设备管理页的展示分叉。

## 模块防火墙自检

- 只改 `shared/helpers/` 与两处测试断言，不跨模块。
- 不改后端、不改接口、不改提交字段。

## Risks / Trade-offs

- [离线设备在下拉里仍可被选中] → 现状如此，本次只收短文案，不改变可选范围；要按在线状态过滤需另开需求。
- [其它未来消费方可能想要状态] → 需要时再加显式参数，而不是靠默认值。

## Migration Plan

改函数 → 改两处断言 → `npx vitest run tests/shared tests/ai-assistant` 与 `npx vue-tsc --noEmit`。回退只需还原一个函数与两处断言。

## Open Questions

无。
