# report-generator · 布局样式与关单附加项

> 归属模块：`frontend/src/modules/report-generator` ｜ 类型：模块功能开发说明
> 代码真相源：`frontend/src/modules/report-generator/index.vue`、`index.style.css`、`constants.ts`、`frontend/src/shared/styles/tokens.css`
> 上级约束：根 `AGENTS.md`、`frontend/AGENTS.md` ｜ 模块索引：`frontend/AGENTS.md`

## 本模块特殊布局/样式（`constants.ts` 为唯一真相源）

- 版式照 BUG 单工作台：WorkbenchHeader + 「报告概览」KPI 三卡 + 「测试报告」分区（FilterTabs 来源筛选 + 关键字/日期 + AppTable 单表 + 前端分页）。
- 模块色 `--c-report`；表纸渐变、徽标、翻页键色值全部取 tokens.css 令牌，去抖 `FILTER_DEBOUNCE`。
- 空态文案：报告在执行完成后生成，引导任务清单 / 平台助手，不提执行引擎。

## 关单附加项（全局清单的 delta）

```
[ ] 常量/文案经 constants.ts，无新魔法字符串
[ ] 报告只读：无写业务数据调用；行点击打开报告文件，路由停留 /reports
[ ] 查看报告复用既有通道，未新拼地址
[ ] npx vitest run tests/report-generator tests/shared/p0/sidebarNavConfig.spec.ts
```
