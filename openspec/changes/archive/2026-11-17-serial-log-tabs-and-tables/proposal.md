# 串口日志：手稿 Tab + 两张表对齐（B 档）

## Why

串口日志页的 Tab 是 Element Plus 蓝色下划线，两张表的首列、状态与操作键仍停留在旧口径；关键词搜索还是原生 input，抽屉里回到 EP small 控件。整页与设备 / BUG 表已经不是一套语言。

## What Changes

- **Tab**：新增模块私有 `SerialLogTabs.vue`（两枚手稿 chip），替换本页的 `AppTabs`；共享件不动。
- **端口表**：列头加图标、首列图标圆、监听状态改 20%→5% 渐变胶囊（开关保留）、操作键换 kit 描边态；新增「只看监听中」筛选与**分页**（10 行/页）。
- **关键词表**：列头加图标、首列图标圆、搜索框换 kit 输入框；计数与来源说明合并成一条说明条。
- **抽屉**：读取行数 / 刷新键收进 `.sketch-kit` 作用域。
- 表纸硬影**保持不变**（去影仍待定，不在本次）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `serial-log-page`：Tab 改为模块私有手稿 chip、刷新键仍留在各面板。
- `serial-log-module`：端口表新增筛选与分页；两张表的字号 / 首列 / 状态胶囊 / 操作键口径。

## Impact

- 前端 `serial-log`：新增 `components/SerialLogTabs.vue`；`index.vue`、`index.style.css`、`WifiPortPanel.vue(+css)`、`LogKeywordPanel.vue(+css)`。
- 不动接口、权限、抽屉取数与关键词只读约束。
