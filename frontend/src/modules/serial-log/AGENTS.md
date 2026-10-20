# serial-log 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `frontend/AGENTS.md` 优先于本文件（本文件只写增量）。

## 入口与布局

- 路由 `/serial-log`（`routes.ts`），侧栏「数据」分组**末尾**（「页面流」之后），标题「串口日志」。
- 页面 = `WorkbenchHeader` + 一条 `AppTabs`，**恰两个 Tab**：`无线端口`（默认）/ `日志关键词`。
- 两个 Tab 的内容分别在 `components/WifiPortPanel.vue`、`components/LogKeywordPanel.vue`，只在选中时挂载；切 Tab **不得**发出写请求。

## 数据与权限

- HTTP 唯一出口是本模块 `api.ts`（走 `shared/api-client`），端点全部在 `/api/serial-log/`：
  - `GET /serial-log/ports/`、`POST /serial-log/ports/toggle/`、`GET /serial-log/ports/{port}/lines/`、`GET /serial-log/keywords/`。
- 监听开关**仅超级管理员**可操作：页面用 `useAuthUser().isSuperuser` 传 `can-manage`；非超管只读并显示「仅超级管理员可以开关监听」。
- 日志窗口只提供刷新 / 调整读取行数；**禁止**新增删除、编辑、下载备份等写入口。

## 样式

- 两个面板都是**多根节点**，页面级 scoped 样式到不了组件内部：区块头 / 按键样式必须由面板自带的 `sl-*` 私有类提供，**禁止**依赖其它模块的样式文件。
- 字号、颜色、间距只用 `shared/styles/tokens.css` 的令牌；表格强调色用 `--c-device`。

## 红线

- **禁止**把这两个面板或它们的来源定义挪回 AI 工具箱：工具箱只保留「平台业务 / 自定义 Skill」两个来源。
- 关键词表**只读**：不提供新增 / 编辑 / 删除 / 上传 / 保存入口，改表仍走 `DEVICE_LOG_KEYWORD_FILE` 指向的文件。
- 不新增第二条采集链路：日志监听、文件格式与轮转都在 `engines/uart_log` / `utils/logs`，本模块只消费。
