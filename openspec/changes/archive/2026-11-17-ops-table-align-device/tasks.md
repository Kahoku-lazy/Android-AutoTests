# 任务：运营两张表对齐设备页

## 1. 令牌与样式底座

- [x] 1.1 新增 `ops-console/table.style.css`（无影表纸、表头居中 + 浅底、正文 14、hover 12% 混底、chip、时间双行、主操作胶囊、⋯、勾选框色）
- [x] 1.2 `index.style.css` 只留页面骨架与两行控制区；删除已迁移的表格 / chip 规则

## 2. 用户管理页

- [x] 2.1 列配置：8 列 → 7 列，每列带 `icon`；首列 `user` 走身份单元
- [x] 2.2 新增 `components/OpsUserIdentityCell.vue`（头像 + 账号 + 邮箱副行）
- [x] 2.3 注册 / 最后登录改双行：相对时间 14 + 绝对时间 12；空值显示「从未登录」
- [x] 2.4 新增 `helpers/datetime.ts`（相对 / 绝对时间，含天 / 月 / 年档）
- [x] 2.5 控制区三行 → 两行；下线行数四键，每页固定 10 条（`OPS_DEFAULT_PAGE_SIZE = 10`，去掉 `setPageSize`）
- [x] 2.6 操作列保留单个「管理」胶囊；表头图标与列名同源渲染
- [x] 2.7 抽屉 chip 皮肤与表格统一（14px / 1.5px 墨边）

## 3. 模型配置页

- [x] 3.1 列配置：6 列 → 5 列（模型首列 / 类型 / 密钥变量 / 地址 / 操作），每列带 `icon`
- [x] 3.2 新增 `components/OpsModelIdentityCell.vue`（模型名 + 厂商 · 类型 · 音色）
- [x] 3.3 类型改 chip（`.ops-kind--chat / --tts / --realtime`）
- [x] 3.4 操作列：`编辑` 胶囊 + `⋯`（`el-dropdown`，删除仍二次确认）
- [x] 3.5 顶部加关键字搜索（前端过滤）

## 4. 测试

- [x] 4.1 `ops-users.spec.ts`：默认 `page_size: 10`，删除已下线的改行数用例
- [x] 4.2 `model-configs.spec.ts`：类型列紧随模型首列；补 `el-dropdown*` 与 `size` 属性 stub
- [x] 4.3 `ops-nav.spec.ts`：侧栏运营三入口不同色（`--c-account` / `--c-element` / `--c-ops`）

## 5. 验证

- [x] 5.1 `npx vitest run tests/ops-console`：4 文件 / 31 用例全绿
- [x] 5.2 `npm run typecheck` 通过；`npm run lint:styles` 无新增违规（存量仅 AppSidebar G13）；`npm run lint:lines` 通过
- [x] 5.3 实跑 computed：`sheetShadow: none` / 表头 `16px` 居中 / 正文 `14px` / 时间 `14 + 12` / 6 个表头图标 / 行数键 0 个
- [x] 5.4 截图对比 `temps/ops-{users,models}-before-after.png`
