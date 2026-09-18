## Context

现状：`element_locator` 用 `Page.parent/is_folder`、`WebGroup`、`ApiGroup` 三套树；前端侧栏三入口。用例管理已落地项目工作台。本设计落地同构 IA，但项目为系统内置三份。动机见 `proposal.md`。

## Goals / Non-Goals

**Goals:**

- 系统三项目 + 统一目录树 + 按域叶子编辑
- 标准信封新 API；旧分组写路径停用
- 迁移保留叶子 ID；检查器/workflow 可继续按 ID 消费

**Non-Goals:**

- 不做跳转流 UI
- 不把三域收成一张「定位文档」表
- 不做 per-user 元素库隔离
- 本期不物理删除 `WebGroup`/`ApiGroup`/Flow 表

## Decisions

1. **项目用 `code` 而非数字 id** — 全站恰好三个，路由与 seed 更稳。备选：数字 id + 固定 seed，多一次查找。
2. **叶子仍用 Page/WebElement/ApiEndpoint** — 避免 dump/Schema 搬家。备选：统一 LocatorFile 表，下游契约风险大。
3. **分组写 → 410，读投影保留** — 防两套树并行写；workflow 选组不立刻断。备选：立刻 404 读也停。
4. **Android 页面作父节点时补同名目录** — 迁移保层级。备选：拍平到根，结构损失。

## 模块防火墙自检

- 跨 App 写只经 `element_locator.api`（检查器导入已如此）
- 禁止他 App import `page_tree` / `api_snapshot`
- dashboard 只读 Model 计数
- 前端只经本模块 `api.ts` → djangoClient；检查器对话框改为本模块封装，禁跨模块 import element-locator/api
- 无新增 WS

## Risks / Trade-offs

- [两套树并行写] → 分组写 410，工作台只写 directories
- [页面父节点迁移变深] → 文档说明同名目录规则
- [workflow web-groups 投影字段不全] → 投影对齐旧只读字段；联调画布选组

## Migration Plan

1. 加表与 directory FK（可空）
2. Seed 三项目
3. Data migration：文件夹/分组 → 目录；叶子挂 directory
4. 部署后前端切新路由；旧写路径 410
5. 回滚：保留旧表，可临时恢复旧前端（目录数据需逆向脚本，成本高，默认不支持热回滚）
