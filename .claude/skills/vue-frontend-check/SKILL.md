---
name: vue-frontend-check
description: |
  Vue 前端代码校验 — 带统一判罚量规：布局裁剪、字号≥12px、硬编码色、DRF契约、展示可达性、DTO/信封。强制逐项记录防同skill结果漂移。
  Keywords: Vue校验, 前端检查, DRF, API契约, 布局裁剪, 字段完整性, 展示组件, vue check, frontend checklist, UI门禁
  Trigger: 用户表达"校验前端/检查 Vue/前端自检/UI 门禁/布局裁剪检查"，或改完 .vue / components / composable / 编辑器后要求确认是否可关单时。
---

# Vue Frontend Check — 前端代码校验门禁

**目的**: 改完 `.vue` / `components/` / composable 后自检。构建通过 ≠ 完成。

**防漂移（必读）**: 同一 skill 两次结果曾不一致 → 判罚必须以 [references/calibration.md](references/calibration.md) 为准，禁止凭感觉升降严重度。

**关联**:
- `frontend/CLAUDE.md` / `frontend/DESIGN_SYSTEM.md`（字号最小 **12px**，禁硬编码 px）
- `dev_docs/项目笔记/前端claude笔记.md`
- `.claude/rules/frontend.md`
- 检查细表 → [references/checklist.md](references/checklist.md)
- **量规/例外/强制输出** → [references/calibration.md](references/calibration.md)

**分层口诀**：`api/` 请求对不对 → `composables/` 状态与流程对不对 → `components/` 看得见的对不对。

## 工作流

```
1. 定范围 + 声明验证方式（静态 | 静态+浏览器）
2. 先跑 calibration §7 强制 rg，再读文件三块
3. 按清单逐项给 ✅/⚠️/❌/N/A（不得只报缺陷）
4. 严重度只准查 calibration §2 表
5. 输出三块：缺陷表 + 逐项记录 + 结论
```

**硬性禁止**:
- 未浏览器验证却把一.1 标 ✅（除非 calibration §3 例外且写明理由；关单仍建议浏览器确认）
- 把 `&lt;12px` 字号标成 🟡
- 只输出缺陷表、省略逐项扫描记录

## 最短路径

```
改 CSS/布局           → 一.1～一.3、一.6～一.7 + 二 + 浏览器缩窗
改 components/        → 一.4～一.5 + 五（含可点击非 button）+ 三.1/三.3
改详情/列表切换       → 三.5 + 四.3 + 五.3
改 composable 传参    → 三.6
改编辑器/保存/API     → 三.7 + 四全部 + 五（若动面板）
任意改动               → 六全部（每次必做，作为三.7 和四.1 的执行细则）
```

## 检查清单（摘要）

细则 → checklist.md；争议口径 → calibration.md。

### 一、模板层（P0）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | 布局裁剪 / 溢出 | 见 calibration §3；主操作区不可被裁死 |
| 2 | Flex 滚动区 | 内部滚动容器：`min-height:0` + overflow 出口 |
| 3 | class ↔ style | 业务 class 有规则 |
| 4 | 字段显示完整性 | 有来源与空值占位 |
| 5 | 表格列截断 | tooltip / title |
| 6 | Dialog/Drawer/Overlay | 内容可滚；主按钮可达 |
| 7 | 视图模式切换布局 | 切换后仍可用 |

### 二、样式层（P1）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | font-size | 必须 `--app-size-*`；**&lt;12px → 🟠**（DESIGN_SYSTEM） |
| 2 | 颜色 | 见 calibration §4（交互 hex/遮罩 🟠；装饰 shadow 🟡） |
| 3 | 行内 style | 静态进 class |
| 4 | 独立 CSS / z-index | 共享 `@import` 可记债；魔法 z-index 须注释 |

### 三、逻辑层（P2）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | 加载/保存/空/错 | 四态可区分 |
| 2 | 响应式安全 | 不丢响应 |
| 3 | 错误处理与文案 | 可见；**禁技术词**（calibration §6） |
| 4 | 空值保护链 | `?.` / 默认值 |
| 5 | 多视图互斥 | 同区状态完备 |
| 6 | composable 入参 | Ref/getter 不混用 |
| 7 | ↔后端协议 | 对照 urls/Serializer/契约；信封正确 |

### 四、模块级（API / 路由 / 保存）

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | DRF 契约 | 路径/方法/字段一致 |
| 2 | DRF 通道 | `api` → `djangoClient` → `/api/...`；禁旁路 |
| 3 | 父子选中/清空 | 双侧+关联上下文 |
| 4 | 路由深链 | 目标对；query 有人读 |
| 5 | 离开守卫 | setup 同步注册 |
| 6 | 体积 | &gt;500 行先拆样式 |
| 7 | 信封解包 | 禁整包当业务对象 |
| 8 | DTO 清洗 | UI-only 不进 payload |
| 9 | 校验/映射 | 校验≥Schema；字段不漏传 |

### 五、展示组件层

| # | 检查项 | 通过标准（要点） |
|---|--------|------------------|
| 1 | 薄组件 | 无 HTTP/重逻辑 |
| 2 | 列表防漂移 | 复用通用壳 |
| 3 | 编辑器 vs 子面板 | 子面板只改自己块 |
| 4～6 | 分块/步骤/列卡详情 | 对齐、不漏字段 |
| 7 | 危险确认 | 删除/移动等有确认 |
| 8 | 锁态禁用 | 只读真正只读 |
| 9 | emits | 与父约定一致 |
| 10 | **可点击可达** | `@click` 在 p/div/span → **🟠**（calibration §5） |

### 六、前后端协议对照（每次必做）

> 本项是三.7 和四.1 的**执行细则**。每次校验必须逐接口做三张对照表，不得只写"已确认"。

**6.1 路径对照表**（每个前端 `api.ts` 函数 ↔ 后端 `urls.py` pattern）

| 前端函数 | HTTP 方法 | 后端路由 | 路径一致 |
|---------|:--:|---------|:--:|
| `apiXxx()` | GET/POST | `apps/xxx/urls.py` → `path(...)` | ✅/❌ |

- 如果前端 `djangoClient` 有 `baseURL`，必须拼接验证完整路径
- 遗漏端点（后端有路由但前端无调用）记 🟡 债
- 路径不一致 → 🔴

**6.2 响应信封对照表**（后端返回体 ↔ 前端解包方式）

对照前先确认后端使用哪种响应方式：

| 后端方式 | 识别特征 | 响应格式 |
|---------|---------|---------|
| DRF `Response()` | 视图继承 `APIView` | 经过 `EnvelopeJSONRenderer` → `{status, data}` |
| Django `JsonResponse()` | 视图用 `@csrf_exempt` + 直接 return | 手动构造，格式不统一 |

- 前端解包代码必须与后端实际格式一致
- 用 `data.data.xxx` 但后端返回顶层字段 → 🔴
- 用 `data.xxx` 但后端套了 `{data: {...}}` → 🔴

**6.3 字段对照表**（后端响应字段 ↔ 前端 TS 类型属性）

逐个对照每个接口的响应字段：

| 接口 | 后端返回字段 | 前端 TS 类型属性 | 类型名 | 一致 |
|-----|-------------|-----------------|-------|:--:|
| `GET /api/xxx` | `status` | `ok` | `ScanResponse` | ❌ |
| `GET /api/xxx` | `message` | `error` | `ScanResponse` | ❌ |

重点检查：
- **字段名**：后端 `status` ↔ 前端类型是否也叫 `status`（不是 `ok`/`success` 等别名）
- **可选性**：后端 `?` 字段 ↔ 前端是否 `optional`
- **嵌套路径**：`data.data.xxx` vs `data.xxx` vs `data.payload.xxx`
- **类型不匹配**：后端 `status: boolean` 但 TS 声明 `ok: boolean` → 🔴（calibration §2）
## 输出格式（强制三块）

```markdown
# Vue 前端校验 — {范围}

验证方式: 静态扫描 | 静态+浏览器
扫描命令: 已执行 calibration §7（是/否）

## 缺陷汇总
| # | 严重度 | 层级 | 文件 | 检查项 | 现象 | 建议 |
|---|--------|------|------|--------|------|------|
| … | 🔴/🟠/🟡 | … | path:Lxx | … | … | … |

## 逐项扫描记录
### 一、模板层
| # | 结果 | 备注 |
| 1 | ✅/⚠️/❌/N/A | … |
（二～五同理，不适用标 N/A）

## 结论
- 通过 / 有条件通过 / 不通过
- 验证方式是否满足关单：是/否
- 阻塞关单项：…
```

## 与其它 skill 分工

| 诉求 | 用哪个 |
|------|--------|
| Vue 关单门禁（本文件） | **vue-frontend-check** |
| Python 质量 | `code-health-check` |
| 功能跑测 | `functional-testing` |
| Vue 写法 | `vue` |
| 设计系统落地 | `frontend-design` |
