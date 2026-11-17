# 用户管理控制区：页码行统一 14px、下线重复的账号计数

## Why

上一轮把控制区收成两行后，第一行右侧留着「共 N 个账号」，第二行左侧又有「第 X / Y 页 · 共 N 条」——同一个数字写了两遍，还占用了批量键那一行的右半边。同时第二行（页码文案 + 筛选 + 搜索 + 翻页）里，页码文案与筛选标签还是 12px，比同一行的搜索框和翻页键小一档，读起来发虚。

## What Changes

- 删除第一行右侧的「共 N 个账号」（与第二行的「共 N 条」重复）。
- 第二行文字统一 **14px**：页码文案 `--app-size-xs` → `--app-size-sm`；`FilterTabs` 在运营作用域内由 12px 提到 14px（共享件不动）。
- 表格内字号不变（表头 16 / 正文 14 / 次级 12）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ops-user-console`：修改「用户列表的表纸、字号与首列身份单元」——控制区第一行不再有账号计数，第二行文字统一 14px。

## Impact

- 前端 `ops-console`：`index.vue`（删一个 `<span>`）、`index.style.css`（页码文案字号 + 运营作用域内的 FilterTabs 覆盖）。
- 不动共享 `FilterTabs.vue`、不动接口与数据。
