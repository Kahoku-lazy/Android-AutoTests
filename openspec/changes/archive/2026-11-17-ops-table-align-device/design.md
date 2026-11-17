# 设计：运营表对齐设备页

## Context

- 两张表都由共享 `AppTable` + `accent="var(--c-ops)"` 渲染；`.wb-shell .sketch-sheet` 提供描边 / 圆角 / 模块色位移硬影。
- `index.style.css` 里账号、邮箱、时间全是 `--app-size-xs`（12px），表头靠全局 `.el-table th`（16px、左对齐）。
- 用户表列定义是「账号 150 / 邮箱 180 / 身份 120 / 状态 100 / 注册 150 / 最后登录 150 / 操作 100」，时间直接喂 `date_joined` 原文。
- 控制区三行：`.doc-section__header`（FilterTabs + 搜索 + 计数）、`.ops-toolbar`（批量键 + 行数四键 + 页码 + 翻页）、表。
- 设备页的既有口径（已归档）：表纸无影、表头 16 + 图标 + 居中、正文 14 / 时间 12、首列身份单元、操作列「主操作胶囊 + ⋯」。

## Goals / Non-Goals

**Goals**：两页与设备页在**表纸、字号档位、首列信息密度、控制区行数**四件事上一致；交互与接口零变化。

**Non-Goals**：不改筛选 / 分页 / 批量语义与接口；不改共享件（`AppTable`、`workbench-theme.css`、`tokens.css`）；不改抽屉里的动作与确认文案；不给模型表加服务端分页。

## Decisions

### D1 表纸去影用模块作用域覆盖，不改共享声明

`.ops-workbench :deep(.sketch-sheet) { box-shadow: none }`——与设备页、BUG 页同一做法。共享 `.sketch-sheet` 还有其它消费方（报告列表等），改共享会让它们一起丢影。

### D2 表格皮肤集中到一个模块样式文件

新增 `ops-console/table.style.css`，被 `index.vue` 与 `model-configs.vue` 各自 `<style src>` 引入（scoped）。两页共用一套：无影、表头居中 + 浅底、正文 14、hover 12% 混底、chip、时间双行、主操作胶囊与 ⋯。避免在两页各抄一份（那就是"第二套皮肤"）。

### D3 用户表首列合并、时间双行

- 首列 `prop: "user"` 走 `OpsUserIdentityCell`：首字母头像（超管 / 运营 / 普通三种底色）+ 账号（等宽 14）+ 邮箱（12 灰）。邮箱不再单独占列，搜索仍支持邮箱（后端 `keyword` 未变）。
- 时间列改 `ops-time`：主行相对时间 14、副行 `YYYY-MM-DD HH:mm` 12；`last_login` 为空时只显示「从未登录」（不出现两行破折号）。
- 相对时间补齐「天 / 月 / 年」档，避免与副行日期重复表达。

### D4 模型表首列与操作列

- 首列 `prop: "model"` 走 `OpsModelIdentityCell`：模型名（等宽 14）+ 「厂商 · 类型（· 音色）」（12 灰）；头像底色随类型走。
- 类型列紧随首列、改为 `.ops-kind` chip（聊天 / 语音合成 / 实时语音三色）。
- 操作列 `编辑` 主操作胶囊 + `⋯` 菜单（`el-dropdown`），删除仍走 `remove()` 的 `ElMessageBox` 二次确认。
- 关键字搜索在前端过滤（`model_name` / `provider` / 类型 / 密钥变量 / 地址），不为 4 条数据加接口参数。

### D5 控制区收两行、行数固定

- 用户表：行 1 = 批量停用 / 批量注销（超管）+ 计数；行 2 = 页码文案 + `FilterTabs` + 搜索 + 翻页。
- `OPS_PAGE_SIZE_OPTIONS` 删除，`OPS_DEFAULT_PAGE_SIZE = 10`；`useOpsUsers` 去掉 `setPageSize`，`pageSize` 变常量参与 `totalPages` 计算。后端 `page_size` 参数仍照传。

### D6 表格必须 `table-layout="fixed"`

实测默认 `auto` 下，模型表「地址」列的不间断 URL 让最小宽度把表格撑宽 46px，`⋯` 被表纸 `overflow: hidden` 裁掉。两页显式 `table-layout="fixed"`，配合 `showOverflowTooltip` 由 tooltip 承担长文本。

## Risks / Trade-offs

- [列变少、行变高]：邮箱移到副行、双行首列把行高推到 ~64px，一屏少 1~2 行 → 可接受，换来扫读性。
- [丢失行数选择]：固定 10 条后 20/50/100 的需求只能翻页 → 与设备 / 任务 / BUG 三页同口径。
- [相对时间口径与设备页不同]：设备页超 1 天回日期，运营页补了「N 天前 / N 个月前」，因为运营页会同时给绝对时间副行，避免两行都写日期。
- [侧栏运营三入口改色]：`ops-nav.spec.ts` 的旧断言（用户管理 = `--c-ops`）与当前 `sidebarNavConfig` 不符，本次一并对齐为 `--c-account` / `--c-element` / `--c-ops`。

## Migration Plan

纯前端模块内改动，无数据迁移。回退 = 还原 `ops-console` 目录下的本次文件与对应 spec 条目。

## Open Questions

无（P0/P1/P2 与字号 16/14/12 已由需求方确认）。
