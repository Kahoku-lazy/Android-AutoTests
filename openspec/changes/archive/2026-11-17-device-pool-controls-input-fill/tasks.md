# 任务：设备页控制条改为输入件皮肤

## 1. 令牌

- [x] 1.1 `shared/styles/tokens.css` 在 `--comp-*` 组新增 `--comp-device-field-fill`（135° 渐变，`--c-device` 45% → 20%，两端 `color-mix` 派生）

## 2. 皮肤

- [x] 2.1 `DevicePoolView.style.css`：把 `.el-select__wrapper`、`.el-input__wrapper` 从按键皮肤块摘出
- [x] 2.2 新增输入件皮肤块：`2px` 墨边、`--app-radius-sm` 圆角、`--comp-device-field-fill` 填充、无影、常规字重、`min-height: 32px`
- [x] 2.3 补 hover / focus：边框转 `--c-dashboard`，focus 加 `0 0 0 3px color-mix(--c-dashboard 20%, transparent)` 环
- [x] 2.4 placeholder 与下拉箭头提到 `--app-text-secondary`（渐变抬亮底色后 EP 出厂灰只剩约 1.7:1）

## 3. 技能登记（偏离回写）

- [x] 3.1 `references/tokens.md` §1.19 记录 `--comp-device-field-fill`
- [x] 3.2 `references/components/form-controls.md` §1 记录「设备页控制条输入件用渐变填充」这一已批准偏离

## 4. 验证

- [x] 4.1 `npm run lint:styles`（无新增违规；存量 `AppSidebar.style.css:209` G13 与本次无关）、`npm run lint:lines` 通过
- [x] 4.2 `node tests/run.mjs module device-pool`：9 个测试文件 / 48 用例全绿
- [x] 4.3 设备页实跑截图 `temps/device-controls-after*.png`：两件无硬影、圆角 `4px 8px`、135° 薄荷绿渐变（computed 值已核）；`上一页/下一页` 仍为按键皮肤
