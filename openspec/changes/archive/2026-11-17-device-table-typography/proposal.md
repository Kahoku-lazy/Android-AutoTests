# 设备表字号：表头 16 / 内容 14 / 时间 12

## Why

设备表与 BUG 表的字号口径现在不一致：设备表表头还是全局默认的 12px，连接 / 可见性胶囊与身份行的序列号仍停在 12px，而同页表格正文是 14px。两页放在一起看，设备表明显更「碎」。

## What Changes

- 表头六个列头统一 **16px**（与 BUG 表同档），并禁止折行。
- 表内其它文本统一 **14px**：设备型号、序列号 / 地址、连接与可见性胶囊、状态标签、分辨率、活跃相对时间、操作胶囊与「⋯」。
- **时间日期 12px**：活跃列的「接入 YYYY-MM-DD HH:mm:ss」。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `device-pool-table`：新增「设备表字号三档」要求（表头 16 / 内容 14 / 时间 12）。

## Impact

- 前端 `device-pool`：`DevicePoolView.style.css`（表头、胶囊、时间）、`components/DeviceIdentityCell.vue`（型号与序列号行）、`components/DeviceActionsCell.vue`（操作胶囊）。
- 不改结构、不改布局、不动共享件与令牌。
