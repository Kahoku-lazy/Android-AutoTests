# 任务：串口日志 B 档

## 1. Tab

- [x] 1.1 新增 `components/SerialLogTabs.vue`（两枚手稿 chip，受控 v-model）
- [x] 1.2 `index.vue` 用它替换 `AppTabs`；`index.style.css` 去掉 `el-tabs` 补丁、加卡头布局

## 2. 端口表

- [x] 2.1 列头 `title + icon`、首列图标圆、监听状态渐变胶囊（开关保留）
- [x] 2.2 操作键换 `DoodleBtn` + 面板挂 `.sketch-kit`（虚线来自 kit）
- [x] 2.3 新增「只看监听中」筛选与计数；分页 10 行/页（常量进 `constants.ts`）

## 3. 关键词表

- [x] 3.1 列头图标 + 首列图标圆（列序已按需求方要求换成「功能点 / 功能模块 / 关键词」，字号随列位对调：首列 16、其余 14）
- [x] 3.2 搜索框换 `el-input`（`.sketch-kit` 作用域）；计数与来源说明合并成说明条
- [x] 3.3 关键词与模块名按功能模块着色：按首次出现顺序取色池，同表内不撞色、搜索不漂移

## 4. 抽屉

- [x] 4.1 读取行数 / 刷新区挂 `.sketch-kit`

## 5. 其他修复

- [x] 5.1 长关键词表被裁：`.serial-log-section` 加 `flex-shrink: 0`，滚动交还 `.doc-body`（实测 70 行可滚到底）
- [x] 5.2 `.sl-btn`（刷新）字号 12 → 14，与卡头 Tab chip 同档
- [x] 5.3 功能模块 / 功能点单元格 12 → 14，与表体同档
- [x] 5.4 删除 `.lk-keyword` 的重复声明（保留一条，合并 `color` 与 `word-break`）

## 6. 验证

- [x] 6.1 浏览器验收 `/serial-log` 两个 Tab：chip 选中态、首列图标圆、状态胶囊 + 开关、只看监听中、分页、模块配色
- [x] 6.2 测试按慢路径修：`LogKeywordPanel.spec` 注册 ElementPlus（真 `el-input`）、`SerialLogPage.spec` stub 换成 `SerialLogTabs`，断言改为新列序
- [x] 6.3 `node tests/run.mjs module serial-log` 30 用例全绿；`prettier --check`、`eslint`、`vue-tsc`、`lint:lines`、`lint:styles`、`openspec validate` 全部通过；截图 `temps/serial-*.png`
