# 设计：串口日志走 B 档

## Context

见 proposal。要点：Tab 是共享 `AppTabs`（EP el-tabs），其它页在用；两张表都在面板里用 `AppTable`，列配置用 `label` 字段；面板私有 `.sl-btn` 提供实线按钮；关键词搜索是原生 `input`；抽屉里有 `el-select size="small"`。

## Goals / Non-Goals

**Goals**：手稿 Tab、表格字号三档与首列身份、状态胶囊、kit 描边键、关键词 kit 搜索、端口筛选与分页、抽屉读取行数控件收进 kit。

**Non-Goals**：不动表纸硬影（去影另议）、不动接口与权限、不改共享 `AppTabs` / `AppTable` / `sketched-kit.css`。

## Decisions

### D1 新增模块私有 `SerialLogTabs.vue`，不动共享件

两枚 chip，受控 `modelValue` + `update:modelValue`。样式只在本组件 scoped 内（墨边、近直角、2px 硬影、选中柠黄），与设备页工具条按键同几何。

### D2 表格列配置从 `label` 迁到 `title + icon`

`AppTable` 支持 `title` 与 `#header-<prop>` 插槽；本页沿用「列头图标 + 纯文字列名」的做法。首列改用新组件内联结构（图标圆 + 主行），不新增第二个表格封装。

### D3 状态 = 渐变胶囊 + 开关并存

开关仍是 `el-switch`（超管可点、非超管禁用），旁边加 `--sp-color` 驱动的渐变胶囊（`linear-gradient(180deg, 20% → 5%)`，文字墨色）。与任务清单状态徽标同一套写法。

### D4 操作键与搜索框都进 `.sketch-kit`

虚线口径只能由 `sketched-kit.css` 声明：面板关键容器挂 `sketch-kit`，按钮用 `DoodleBtn tone="paper"`，关键词搜索用 `el-input`（自动得到虚线框）。

### D5 端口表筛选与分页复用共享 `usePagination`

筛选用本地 `onlyListening` 布尔，分页用 `usePagination(filtered, { pageSize: 10, options: [10] })`；行数常量落 `serial-log/constants.ts`（`PORTS_PAGE_SIZE` / `PORTS_PAGE_SIZE_OPTIONS`）。

### D6 刷新键留在各自面板

原计划上提到卡头，但会改动两个面板的职责边界（谁负责取数）；本次保持「谁的数据谁刷新」，卡头只放 Tab。

## Risks / Trade-offs

- [`.sketch-kit` 作用于面板容器，会同时影响面板内 el-switch 之外的输入控件] → 面板内目前没有其它输入控件，风险可控。
- [端口表新增分页后，计数与筛选条并存] → 计数放在筛选条右侧，格式「命中/总数」。

## Migration Plan

纯前端；新增组件可整体删除回退。

## Open Questions

- 表纸是否去硬影（pending 需求方）。
