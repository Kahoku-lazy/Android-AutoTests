# report-generator 模块 CLAUDE.md

> 全局边界 / 模板样式 / 协议要点 / 关单清单 → `../../CLAUDE.md`；本文只写本模块增量，冲突以全局为准。

## 红线（全局表 report-generator 行的展开）

| 只做 | 禁止 |
|------|------|
| 报告列表/KPI/趋势/详情/文件下载 | 生成报告文件 / 写业务数据 / 下载走 JSON api（用 FileResponse `fetch().text()`） |

- **报告下载是 FileResponse 非 JSON，必须用 `fetch().text()` 而非 `api()`**，否则报告内容乱码。
- `STATUS_LABEL_MAP` 双口径（`api.ts` 与 `constants.ts` 各一份）是已登记收敛项，待后端枚举合并后收敛，**禁止新增第三份映射**。

## 本模块契约

**信封特例（非全局 `{status, data}`）**：`/reports/*` 响应为**平铺**、各端点结构不同（列表 `{status, summary, trend, runs}`、详情 `{status, run:{}}`、任务 `{status, task:{}}`），前端按端点结构读取；状态枚举透传 `TestRunRecord.status`（大写）。已登记 ARCH-07 §4 / PRD-07 §5 章首，禁止在未收敛前改成信封式。

- 列表 / 用例分解：`GET /reports` · `GET /reports/cases`（`result` 参数）
- 详情：`GET /reports/run/{runId}` · `GET /reports/task/{taskId}`
- 内容（JSON api）：`GET /reports/{filename}/content`；**下载 URL**：`/api/reports/{filename}`（FileResponse，`fetch().text()`）

## 本模块特殊布局/样式（`constants.ts` 为唯一真相源）

- 表格布局尺寸 `TABLE_*`、图表配置 `CHART_*`（色值走 `CHART_COLORS`，JS 画布例外）、去抖 `FILTER_DEBOUNCE`/`CHART_RESIZE_DEBOUNCE`、阈值 `PASS_RATE_*`

## 关单附加项（全局清单的 delta）

```
[ ] 文件下载走 fetch().text()，未误用 JSON api()
[ ] STATUS_LABEL_MAP 双口径未新增第三份映射
[ ] 常量/阈值经 constants.ts，无新魔法字符串
[ ] 报告只读：无写业务数据调用
```
