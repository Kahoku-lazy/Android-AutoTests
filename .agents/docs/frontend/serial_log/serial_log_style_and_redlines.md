# serial-log · 样式与红线

> 归属模块：`frontend/src/modules/serial-log` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/serial-log/index.style.css`、`components/WifiPortPanel.vue`、`components/LogKeywordPanel.vue`、`frontend/src/shared/styles/tokens.css`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 样式

- 两个面板都是**多根节点**，页面级 scoped 样式到不了组件内部：区块头 / 按键样式必须由面板自带的 `sl-*` 私有类提供，**禁止**依赖其它模块的样式文件。
- 字号、颜色、间距只用 `shared/styles/tokens.css` 的令牌；表格强调色用 `--c-device`。

## 红线

- **禁止**把这两个面板或它们的来源定义挪回 AI 工具箱：工具箱只保留「平台业务 / 自定义 Skill」两个来源。
- 关键词表**非超管只读**：普通用户无新增 / 编辑 / 删除入口；超级管理员可经页面新建 / 编辑 / 删除（表单弹窗 + 行内操作），写入经后端 `serial_log/api.py`；真相源为数据库 `sl_log_keywords`。
- 不新增第二条采集链路：日志监听、文件格式与轮转都在 `engines/uart_log` / `utils/logs`，本模块只消费。
