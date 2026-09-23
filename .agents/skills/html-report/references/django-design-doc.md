# Django 后端方案设计文档 — 章节契约与骨架

> 本文件给 `html-report` 补上「**后端 Django 方案设计该写什么**」。本 skill 主体只讲怎么把 HTML 画得合规，这里讲内容该有哪些章、每章的判据是什么、怎么机械核对。
> 视觉规范仍以 `references/PROMPT.md` 为准；本文件只补**内容契约**。

## 0. 产物落位与三种产物的边界

产物按项目文档位置约定存放。命名 `设计方案-<主题>.html` / `报告-<主题>.html`。

| 产物 | 何时写 | 参照 |
| --- | --- | --- |
| **方案设计**（本文件） | 动手**前**，给人评审 | 时态 = 将实现 |
| 检查报告 | 落地**后**，实测对照 | `报告-Django设计系统分层D0-D5检查.html` 是范例，时态 = 已实现 |
| 接口文档 | 契约定稿后 | `API-*.md` |

两条纪律：**方案设计不得把"已实现"写成"将实现"**（时态诚实，否则评审是在评一个幻影）；**方案设计不替代接口文档**——它写"契约将是什么"，接口文档写"契约现在是什么"。

## 1. 必填章节（12 章）

| # | 章节 | 写什么 | 判据 / 真相源 |
| --- | --- | --- | --- |
| 1 | 背景与目标 | 为什么改、达成什么、追到需求编号 | `PRD-*.md` / OpenSpec change |
| 2 | 影响面 | App · Model · 表 · 端点 · 前端契约 · 通道，一张表说完 | 对应 App 的约束与契约段 |
| 3 | 分层落位 D0–D5 | 每层改什么、**哪些层明确不动** | 平台总体架构的分层约定 |
| 4 | 数据模型与迁移 | 表名（含前缀）· `db_table` 显式 · 字段 · 索引 · 唯一约束 · 迁移文件 | 表前缀 `dp_ di_ el_ cm_ tr_ rg_ ai_ ev_ wf_` |
| 5 | API 契约 | 每个端点：方法 / 路径 / 入参 / 出参信封 / 错误码 | `urls.py` 是路径真相源 → View → Serializer → `api.py` |
| 6 | 写库与模块边界 | 每个写操作落在哪个 App 的 `api.py` | 写库收敛与防火墙 #1/#2 |
| 7 | 通道与协议 | 走 HTTP / WS / AI Tool / 下载 中的哪条 | 四条通信通道 |
| 8 | 鉴权与安全 | 身份从哪来、公开路径有哪些 | `request.user_id`（中间件注入）；`gateway/middleware.py` 的 `_is_public()` |
| 9 | 兼容与回滚 | 迁移可逆性、是否双写/回填、旧契约保留期 | — |
| 10 | 测试与验收 | 本方案将跑哪些**具体命令** | 后端关单清单（见 `django-backend-check` skill） |
| 11 | 批次与顺序 | P0 / P1 / P2 + **明确不做** | — |
| 12 | 风险与未知 | 不掩盖；标注"待验证" | — |

### 第 5 章（API 契约）是不可省的一半

后端方案评审失败，多半是这一章写成了散文。**逐端点列表**，每行至少五格：

| 方法 | 路径 | 入参 | 出参（信封内 `data`） | 错误码 |
| --- | --- | --- | --- | --- |
| `POST` | `/api/devices/connect/` | `device_id`, `timeout` | `{status:"ok", data:{session_id}}` | 400 / 404 / 409 / 500 |

三条硬约束：

1. **信封**：`{status, data}` 或 `{status, message}`。特例（report_generator `/reports/*` 平铺 + `FileResponse`、workflow 非 router 路径平铺）**禁止新增**，未收敛前也禁止改造成信封式。
2. **命名**：HTTP JSON 一律 **snake_case**；camelCase 转换发生在前端侧，后端不为前端改名。
3. **双边同步**：改路径或字段，必须同时改 前端 api 层 + 接口文档 + 本 App Serializer，三处缺一即不合格。

> ⚠️ 接口文档命名统一为 `API-*.md`，以实际落盘位置为准，不要照抄过时路径。

## 2. 自包含 HTML 骨架

这是从既有 `报告-Django设计系统分层D0-D5检查.html` 抽出的**已验证骨架**。直接复制，别重新发明。

### ⚠️ 这是「令牌子集」变体，不是 PROMPT.md 的 inline-HTML 模式

必须先讲清一个差异，否则会照错规范：

| | PROMPT.md 描述的 inline-HTML 模式 | 既有 Django 报告的实际做法 |
| --- | --- | --- |
| 技术栈 | React 18 + Babel-standalone（unpkg CDN）+ JSX | **纯 HTML + vanilla CSS**，无任何 CDN JS |
| 组件 | 必须手搓同名 React 组件（`Card`/`Title`/`Button`…），**禁止**裸 `<button>`/`<input>` | 直接用 `.card` `.callout` `table` 等类名 |
| 取用范围 | 完整 26 组件 + 硬性规则 | **只取 design token + 少数布局类** |

**后端方案设计文档沿用既有的「令牌子集」变体**，理由：方案文档要能离线打开、能被 git diff、不依赖 unpkg 可用性；引一套 React 运行时去渲染一份静态设计文档，收益为零而脆弱性大增。

因此本变体下：PROMPT.md 的**颜色 / 字体 / 圆角 / 阴影 / 动画 / 自包含** 6 类硬性规则**继续适用**；而「必须手搓 React 组件、禁止原生标签」这条**不适用**（本变体本就不产生交互组件）。

骨架如下：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>设计方案 · {主题}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{
  --primary:#19c8b9; --primary-hover:#3dd4c6; --primary-active:#11a89b; --primary-bg:#e6f9f6;
  --text:#794f27; --text-body:#725d42; --text-secondary:#9f927d; --text-muted:#8a7b66;
  --bg:#f8f8f0; --bg-content:rgb(247,243,223); --bg-disabled:#f0ece2;
  --border:#c4b89e; --border-hover:#a89878; --border-strong:#9f927d;
  --shadow-btn:#bdaea0;
  --success:#6fba2c; --warning:#f5c31c; --error:#e05a5a;
  --focus-yellow:#ffcc00;
  --r-sm:12px; --r-base:18px; --r-lg:24px; --r-pill:50px;
  --ease:cubic-bezier(0.4,0,0.2,1);
  --D0:#889df0; --D1:#82d5bb; --D2:#f7cd67; --D3:#e59266; --D4:#b77dee; --D5:#fc736d;
  --mono:"SF Mono","Fira Code","Cascadia Code",Consolas,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Nunito,"Noto Sans SC",-apple-system,"PingFang SC",sans-serif;font-weight:500;letter-spacing:.01em;background:var(--bg);color:var(--text-body);line-height:1.6}
:focus-visible{outline:2px solid var(--focus-yellow);outline-offset:2px}
/* heraldic ribbon 页标题（硬性规则 7 要求，不要换成 blob/pill） */
.ribbon{--rb:#e0a92e;--rk:#b9881f;display:inline-flex;align-items:center;position:relative;height:2em;padding:0 1.6em;background:#f7cd67;color:var(--text);font-weight:900;font-size:26px;line-height:1;letter-spacing:.03em;filter:drop-shadow(0 .08em .12em rgba(0,0,0,.05))}
.ribbon-back{position:absolute;bottom:-.4em;width:1.7em;height:1.7em;background:var(--rb);z-index:1}
.ribbon-back.left{right:100%;clip-path:polygon(100% 0%,100% 100%,0% 100%,30% 50%,0% 0%)}
.ribbon-back.right{left:100%;clip-path:polygon(0% 0%,100% 0%,70% 50%,100% 100%,0% 100%)}
.ribbon-fold{position:absolute;top:calc(100% - .04em);width:0;height:0;z-index:2}
.ribbon-fold.left{left:0;border-width:0 .95em .45em 0;border-style:solid;border-color:transparent var(--rk) transparent transparent}
.ribbon-fold.right{right:0;border-width:.45em 0 0 .95em;border-style:solid;border-color:var(--rk) transparent transparent transparent}
.ribbon-text{position:relative;z-index:5;font-weight:900;padding-top:.05em}
.page{max-width:1180px;margin:0 auto;padding:40px 32px 64px}
.lede{color:var(--text-secondary);font-size:14px;margin:14px 0 22px;max-width:940px}
.mono{font-family:var(--mono);font-size:12.5px;font-weight:600;color:var(--text);background:var(--bg-disabled);padding:1px 6px;border-radius:6px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:28px}
.kpi{background:var(--bg-content);border:2px solid var(--border);border-radius:var(--r-base);padding:16px 18px;border-left:8px solid var(--primary);transition:transform .15s var(--ease)}
.kpi:hover{transform:translateY(-2px)}
.kpi b{display:block;font-size:22px;font-weight:900;color:var(--text);letter-spacing:.02em}
.kpi span{font-size:12px;font-weight:700;color:var(--text-muted)}
.kpi.ok{border-left-color:var(--success)}
.kpi.warn{border-left-color:var(--warning)}
.kpi.bad{border-left-color:var(--error)}
.card{background:var(--bg-content);border:2px solid var(--border);border-radius:var(--r-base);padding:18px 20px}
.callout{border-left:8px solid var(--primary);background:var(--bg-content);border-radius:var(--r-base);padding:16px 20px;font-size:13.5px}
h2{font-weight:800;font-size:19px;color:var(--text);letter-spacing:.02em;margin:28px 0 12px;display:flex;align-items:center;gap:10px}
h2 .dot{width:10px;height:10px;border-radius:50%;background:var(--primary);box-shadow:0 0 0 4px var(--primary-bg)}
.tbl-wrap{overflow-x:auto;border-radius:var(--r-base)}
table{width:100%;border-collapse:collapse;background:var(--bg);border:2px solid var(--border-strong);border-radius:var(--r-base);overflow:hidden;font-size:13px}
thead th{background:linear-gradient(180deg,#f2ecd8,#ece4cc);color:var(--text);font-weight:800;text-align:left;padding:10px 12px;border-bottom:2px solid var(--border)}
tbody td{padding:9px 12px;border-bottom:1px dashed var(--border);vertical-align:top}
tbody tr:nth-child(even){background:rgba(196,184,158,.12)}
.tag{display:inline-block;font-size:10.5px;font-weight:900;letter-spacing:.04em;padding:1px 7px;border-radius:var(--r-pill);background:var(--bg-content);border:1.5px solid var(--border-strong);color:var(--text)}
.tag.ok{border-color:var(--success);background:#eef8e4}
.tag.warn{border-color:var(--warning);background:#fdf6dd}
.tag.bad{border-color:var(--error);background:#fdecec}
ul.checks{list-style:none}
ul.checks li{position:relative;padding:9px 12px 9px 38px;border-bottom:1px dashed var(--border);font-size:13.5px}
ul.checks li:last-child{border-bottom:none}
ul.checks li::before{position:absolute;left:12px;top:9px;font-weight:900}
ul.checks li.ok::before{content:"\2714";color:var(--success)}
ul.checks li.risk::before{content:"\26A0";color:#c9a00a}
ul.checks li.bad::before{content:"\2716";color:var(--error)}
footer{margin-top:40px;padding-top:16px;border-top:2px dashed var(--border);font-size:12.5px;color:var(--text-muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
@media (max-width:768px){.page{padding:24px 16px 40px}.kpis{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="page">
  <!-- 用 .ribbon（heraldic ribbon，见既有报告的 .ribbon 全家桶）做页标题，不要用 blob/pill -->
  <span class="ribbon"><span class="ribbon-text">设计方案 · {主题}</span></span>
  <p class="lede">{一句话目标} · 对照源码与 {ARCH/PRD 编号} · {日期}</p>

  <div class="callout"><b>结论先行</b>：{方案主张一句话}。</div>

  <h2><span class="dot"></span>一、背景与目标</h2>
  ...
</div>
</body>
</html>
```

**已知缺口**：既有骨架**没有** `@media print` 规则，而 `SKILL.md` 的输出自检清单要求「打印: 去除背景色和阴影」。生成时请补一段，别照抄缺口：

```css
@media print{body{background:#fff}*,*::before,*::after{box-shadow:none!important}.kpi,.card,.callout,table{background:#fff!important}}
```

**布局与组件**：KPI 摘要用 4 列 `.kpis`（`.kpi` + `.ok/.warn/.bad` 左边框色带）；表格用 `.tbl-wrap > table` + `.tag` 标状态；核对清单用 `ul.checks`（`li.ok/.risk/.bad` 自动打 ✔/⚠/✖）；结论与上下文用 `.callout` 左边框色带（teal = 结论）。页脚给生成时间戳与"本文档未改代码"声明。

## 3. 硬性核对清单

生成后端方案设计 HTML 后逐条自查：

```
[ ] 时态诚实：已实现 / 将实现 分开写，不把现状写成计划
[ ] 12 章齐备（或明确说明某章为何不适用）
[ ] 每个端点都写了 方法/路径/入参/出参信封/错误码
[ ] 每个新表都写了 表名（含前缀）/ db_table / 索引 / 迁移
[ ] 写操作逐条指明落在哪个 App 的 api.py
[ ] 跨 App 写未走对方 api 的条目 = 0
[ ] 未新增 legacy 平铺信封特例
[ ] HTTP JSON 字段为 snake_case
[ ] 动了 Model → 方案里已列迁移与 makemigrations --check
[ ] WS 涉及 → 已说明 gateway/routing.py 注册与事件 type
[ ] 「明确不做」已列出
[ ] 视觉过本 skill 14 条硬性规则（配色/圆角/阴影/动画/自包含）
```

## 4. 与其他 skill 的分工

| 阶段 | 用什么 |
| --- | --- |
| 动手**前**方案设计（本文件） | `html-report` + `references/django-design-doc.md` |
| 落单 | `openspec-propose` |
| 落地 | `openspec-apply-change` |
| 关单门禁（check / ruff / 迁移 / 信封 / api.py 契约 / 静默吞错 / 体积） | `django-backend-check` |
| 边界 · 防火墙 #1~#4 · 体积阶梯 | `boundary-check` |
| 前端配套方案（界面原型） | `frontend-change-plan` |

**本文件不负责验收**。方案里承诺的命令，落地后由 `django-backend-check` 逐条复核。
