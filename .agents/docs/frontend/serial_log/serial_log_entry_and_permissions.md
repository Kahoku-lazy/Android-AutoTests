# serial-log · 入口、Tab 与权限

> 归属模块：`frontend/src/modules/serial-log` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/serial-log/index.vue`、`api.ts`、`routes.ts`、`components/SerialLogTabs.vue`、`components/WifiPortPanel.vue`、`components/LogKeywordPanel.vue`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 入口与布局

- 路由 `/serial-log`（`routes.ts`），侧栏「数据」分组**末尾**（「设备管理」之后），标题「串口日志」。
- 页面 = `WorkbenchHeader` + 卡头一条**模块私有** `SerialLogTabs`（手稿 chip；不用共享 `AppTabs`，那是 EP 蓝色下划线），**恰两个 Tab**：`无线端口`（默认）/ `日志关键词`。
- 两个 Tab 的内容分别在 `components/WifiPortPanel.vue`、`components/LogKeywordPanel.vue`，只在选中时挂载；切 Tab **不得**发出写请求。

## 数据与权限

- HTTP 唯一出口是本模块 `api.ts`（走 `shared/api-client`），端点全部在 `/api/serial-log/`：
  - `GET /serial-log/ports/`、`POST /serial-log/ports/`、`POST /serial-log/ports/toggle/`、`PATCH /serial-log/ports/{port}/`、`DELETE /serial-log/ports/{port}/`、`GET /serial-log/ports/{port}/lines/`、`GET /serial-log/keywords/`。
- 监听开关与自定义端口的新增 / 编辑 / 删除**仅超级管理员**可操作：页面用 `useAuthUser().isSuperuser` 传 `can-manage`；非超管只读并显示「仅超级管理员可以开关监听」。配置端口三列只读；自定义端口可编辑 SKU / 波特率（端口号不可改）与删除（删除保留日志文件）。
- 日志窗口只提供刷新 / 调整读取行数；**禁止**新增删除、编辑、下载备份等写入口。
