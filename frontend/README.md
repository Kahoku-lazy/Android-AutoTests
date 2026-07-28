# 前端文档导航

> Android-AutoTests 前端：Vue 3 + Vite + Element Plus · Doodle Craft 主题 · 9 模块  
> 最后更新：2026-07-27

---

## 场景速查

| 我要做什么 | 读这份文档 |
|-----------|-----------|
| 新页面 / 新组件 / 改样式 | `DESIGN_SYSTEM.md` → 查色板、组件模板、页面骨架 |
| 改前端前先了解规则 | `CLAUDE.md`（本目录）→ 改前四步工作流 |
| 了解架构红线 / 三层职责 / 文件上限 | `../.claude/rules/frontend.md` |
| 查前后端接口字段名 | `../dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` |
| 改完代码后自检质量 | `../dev_docs/DEVELOPMENT_CHECKLIST.md`（7 组 35 条） |
| 排查前端故障 | `../.claude/rules/troubleshooting.md` → 速查表 → 对应章节 |
| 了解某个模块的功能与验收条件 | `../dev_docs/02-PRD需求/PRD-0X-模块名.md` |
| 了解某个模块的架构与组件树 | `../dev_docs/03-设计与架构/ARCH-0X-模块名.md` |
| 选侧边栏主题 | `.claude/skills/sidebar-themes/SKILL.md` |
| 查 Vue 3 写法参考 | `.claude/skills/vue/references/` |

---

## 文档清单（按层级）

### 第一层：入口指令（1 个文件）

| 文件 | 说明 |
|------|------|
| `../CLAUDE.md`（项目根） | 全项目行为准则、开发铁律、模块防火墙 |

### 第二层：架构约束（3 个文件）

| 文件 | 说明 |
|------|------|
| `../.claude/rules/frontend.md` | 前端架构红线、三层职责、组件拆分信号、质量门禁 |
| `../.claude/rules/conventions.md` | 命名规范、文件行数上限、Element Plus 陷阱 |
| `../.claude/rules/api-conventions.md` | API 响应格式 `{ok, data/error}`、模块边界三道防火墙 |

### 第三层：前端工作流 + 设计系统（3 个文件）

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | 改前四步、CSS 替换流程、HTTP/WS/SSE 三协议、验证清单 |
| **`DESIGN_SYSTEM.md`** | Doodle Craft 主题唯一真相源：7 节/色板/组件模板/页面骨架/工程约束 |
| `src/shared/styles/tokens.css` | CSS 变量唯一真相源（238 行） |

### 第四层：接口契约 + 质量门禁（2 个文件）

| 文件 | 说明 |
|------|------|
| `../dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` | 前后端 REST + WebSocket + SSE 交互契约 |
| `../dev_docs/DEVELOPMENT_CHECKLIST.md` | 7 组 35 条自检（含第 7 组 DESIGN_SYSTEM 合规） |

### 第五层：PRD + ARCH（16+ 个文件）

| 模块 | PRD | ARCH |
|------|-----|------|
| 仪表盘 | `PRD-00-仪表盘.md` | `ARCH-07-仪表盘.md` |
| 设备管理 | `PRD-01-设备管理.md` | `ARCH-02-设备管理.md` |
| 元素定位 | `PRD-02-元素定位.md` | `ARCH-01-元素定位.md` |
| 用例管理 | `PRD-03-用例管理.md` | `ARCH-03-用例管理.md` |
| 执行引擎 | `PRD-04-执行引擎.md` | `ARCH-04-执行引擎.md` |
| 测试报告 | `PRD-05-测试报告.md` | `ARCH-05-测试报告.md` |
| AI 助手 | `PRD-06-AI助手.md` | `ARCH-06-AI助手.md` |
| 工作流工作台 | `PRD-08-工作流工作台.md` | `ARCH-08-工作流工作台.md` |

路径前缀：PRD → `../dev_docs/02-PRD需求/` | ARCH → `../dev_docs/03-设计与架构/`

### 第六层：问题管理 + 技术债（3 个文件）

| 文件 | 说明 |
|------|------|
| `../dev_docs/05-开发与测试/平台级/前端技术债清理SPEC.md` | 全量扫描 7 条清理线 + 5 阶段执行路线 |
| `../dev_docs/05-开发与测试/问题管理/联调功能-AI助手模块化重构方案.md` | AI 助手模块重构设计计划（待执行） |
| `../dev_docs/05-开发与测试/问题管理/联调功能-AI助手模块问题记录.md` | AI 助手 41/43 问题未解决（含 7 CRITICAL） |

### 第七层：Skill 知识库（6 个 Skills）

| Skill | 路径 | 触发场景 |
|------|------|------|
| frontend-design | `.claude/skills/frontend-design/SKILL.md` | 新页面/新组件/改样式 |
| vue | `.claude/skills/vue/SKILL.md` | Vue 3 开发参考 |
| ui-ux-pro-max | `.claude/skills/ui-ux-pro-max/SKILL.md` | UI/UX 设计 |
| sidebar-themes | `.claude/skills/sidebar-themes/SKILL.md` | 侧边栏主题选型 |
| web-design-guidelines | `.claude/skills/web-design-guidelines/SKILL.md` | Web 设计指导 |
| prototype-design | `.claude/skills/prototype-design/SKILL.md` | 高保真原型 |

---

## 变更前端代码的标准流程

```
1. 读 frontend/CLAUDE.md → 改前四步
2. 改样式 → 查 frontend/DESIGN_SYSTEM.md
3. 改 API → 查 dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md
4. 改完 → 跑 dev_docs/DEVELOPMENT_CHECKLIST.md 第 7 组（DESIGN_SYSTEM 合规）
5. 构建 → cd frontend && npx vite build --mode development
6. 浏览器验证实际页面（非原型 HTML）
```

---

## 2026-07-27 文档整合记录

本次整合删除了 6 个已被吸收的冗余文档：

| 删除 | 原因 |
|------|------|
| 4 个前端问题管理文档（Tabs滚动/图表滚动/页面滚动/表格列宽） | 修复方案已吸收至 `DESIGN_SYSTEM.md` §4.4、§5.2 |
| `截图流故障手册.md` | 内容已吸收至 `.claude/rules/troubleshooting.md` §二 |
| `前端笔记.md` | 结构化内容与 `CLAUDE.md` + `frontend.md` 重复；文档清单由此 README 替代 |

同时补强了：
- `DEVELOPMENT_CHECKLIST.md` — 新增第 7 组（DESIGN_SYSTEM 合规 7 项）
- `VUE_API_CONTRACT.md` — 补 workflow + AI 助手端点 + SSE 事件表 + 时效标记
- `PRD-08-工作流工作台.md` — 8 项已完成功能标注验收日期
- 8 个 ARCH 文件 — 全部标注前端架构基线 v1.0
