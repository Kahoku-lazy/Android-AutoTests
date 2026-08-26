# Vue 前端校验 — 完整检查表

> 由 `SKILL.md` 按需加载。判罚争议以 [calibration.md](calibration.md) 为准。

## 一、模板层（P0）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 布局裁剪 / 溢出 | 浏览器缩窗 + 侧栏；`rg overflow` | 主操作区不被裁死；见 calibration §3 | 表单容器 `overflow:hidden`；无滚动出口 |
| 2 | Flex 滚动区 | 查滚动容器 CSS | `min-height:0` + overflow 出口 | 仅 `flex:1` 撑破不滚 |
| 3 | class ↔ style | 模板 class 对照 style | 业务 class 有规则 | 漏 inner class |
| 4 | 字段显示完整性 | 绑定 ↔ API/赋值 | 有来源与空值占位 | 编辑页空白表单 |
| 5 | 表格列截断 | 长文本列 | tooltip / title | 无 show-overflow-tooltip |
| 6 | Dialog/Drawer/Overlay | 长文案 + 矮视口 | 内容可滚；主按钮可达；静态判 ❌ 须满足 calibration §3.1 全部条件，否则最多 ⚠️ | 错误卡无 max-height；v-for 无上限撑爆弹层 |
| 7 | 视图模式切换 | 卡片↔表格等 | 切换后仍可用 | 叠层/塌陷 |

> 未浏览器验证：一.1 不得 ✅（最多 ⚠️）。

## 二、样式层（P1）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | font-size | `rg "font-size:\\s*\\d+px"` | `--app-size-*`；**&lt;12px→🟠** | `10px` |
| 2 | 颜色 | calibration §4 | 交互 hex/遮罩→🟠；装饰 shadow→🟡；`var(--t,#fb)` 主值 token→✅ | `color:#fff` |
| 3 | 行内 style | 搜 `style=` | 静态进 class | 可 class 化却行内 |
| 4 | 独立 CSS / z-index | 查 `@import` / z-index | 共享 css 可记债；z-index 有注释 | `9999` 无说明 |
| 5 | 圆角 | `rg "border-radius"` | 不对称；对称大圆角 `50px/16px/20px` → 🟠 | `border-radius:16px` |
| 6 | 阴影 | `rg "box-shadow"` | 扁平 `2px 2px 0`；模糊/大扩散 → 🟡 | `0 8px 24px rgba(...)` |
| 7 | 间距 | `rg "padding\|gap\|margin"` | `--app-space-*`；裸 px → 🟡 | `gap:20px` |
| 8 | 模块色 | 对照 DESIGN_SYSTEM §1.2/1.3 | 用对应 `--c-*`/`--app-status-*`；用错 → 🟠 | 设备用 `--c-dashboard` |
| 9 | 禁止事项 | `rg "backdrop-filter\|#4a4e69\|#9a8c98"` | 无玻璃态/旧色值 → 🟠 | `backdrop-filter:blur(2px)` |

## 三、逻辑层（P2）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 加载/保存/空/错 | 四态分支 | 可区分 | 只有成功路径 |
| 2 | 响应式安全 | 解构 / `?.` | 不丢响应 | props 解构丢更新 |
| 3 | 错误文案 | catch / status false | 可见；禁技术词（calibration §6） | 「请检查后端是否启动」 |
| 4 | 空值保护 | API→模板 | 有兜底 | `.map` 无 `\|\|[]` |
| 5 | 多视图互斥 | v-if 状态表 | 互斥完备 | 详情+列表叠层 |
| 6 | composable 入参 | 实参 vs 内部取值 | Ref/getter 不混 | 函数当 Ref |
| 7 | ↔后端协议 | urls/Serializer/契约 | 路径方法字段+信封一致 | lock 路径错 |

## 四、模块级补充

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | DRF 契约 | urls + Serializer | 一致 | export 路径错 |
| 2 | DRF 通道 | HTTP 出口 | api→djangoClient→/api | 直连 :8766 |
| 3 | 父子选中/清空 | 返回/clear | 双侧+关联上下文 | 只清本地 |
| 4 | 路由深链 | routes/query | 有人读 query | tab 写入不读 |
| 5 | 离开守卫 | leave 位置 | setup 同步 | onMounted 注册 |
| 6 | 体积 | 行数 | &gt;500 先拆样式 | 单文件上千行 |
| 7 | 信封解包 | 赋值 | 拆 status/data | 整包当 definition |
| 8 | DTO 清洗 | save/toRaw | 无 UI-only | `_meta` 进 payload |
| 9 | 校验/映射 | vs Schema | 校验≥Schema | 只验标题 |

## 五、展示组件层

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 薄组件 | script | 无 HTTP/重逻辑 | 组件内拼 payload |
| 2 | 列表防漂移 | *CaseList | 复用通用壳 | 四份复制 |
| 3 | 编辑器 vs 子面板 | 职责 | 子面板只改自己块 | 旁路保存 |
| 4 | 分块面板 | 结构对齐 | 不串写 | validation 进 steps |
| 5 | 步骤类型字段 | StepEditor | 字段+必填齐 | 缺字段 |
| 6 | 列/卡/详情 | 对照 | 关键字段不漏 | 卡无锁定 |
| 7 | 危险确认 | 删除/移动等 | 有确认 | 一点即删 |
| 8 | 锁态禁用 | locked | 真正只读 | 能改却保存失败 |
| 9 | emits | 事件名 | 与父一致 | 未 clear-case |
| 10 | 可点击可达 | `@click` 非 button/a | 否则 **🟠** | `<p @click>去注册` |

## 常用扫描命令

见 [calibration.md](calibration.md) §7（含逻辑/协议类补充；Windows 无 `rg` 时用内置 grep 工具等价执行）；另可：

```bash
rg -n "overflow|el-dialog|el-drawer" path/to/
rg -n "show-overflow-tooltip|ConfirmButton|locked" path/to/
rg -n "clear-case|refresh-tree" path/to/
rg -n "_meta|toRaw\(|config_json" path/to/
rg -n "const \{[^}]*ok," path/to/   # 视图数据流走查：解包字段名 vs 后端信封
```

## 数据流走查（六.4 的执行细则，逐视图必做）

按视图逐个走查 `fetch → 解包 → 赋值 → 渲染`（读方向）与 `表单 → payload → 后端语义`（写方向），禁止只查 api 层就下结论：

| 步 | 走查点 | 反例（实测） |
|----|--------|--------------|
| 1 | api 函数返回体 = 后端信封原样？ | 声明类型与后端字段不符，靠 `as` 强转掩盖 |
| 2 | 视图解包的字段名与后端一致？ | `{ok, data}` 解包 `{status, data}` → `ok` 恒 undefined |
| 3 | 嵌套路径正确？ | 后端 `data:{documents}` 却读顶层 `documents` |
| 4 | 赋值后模板真能渲染？ | `if(ok)` 恒假 → 状态卡永远「—」 |
| 5 | **写方向**：save payload 的字段语义 = 后端 update 语义？ | 编辑模式发 `tools:[]`，后端 `_sync_agent_tools` 视为清空 → 保存即删光工具 |

## SSE 与文件下载（六.5 / 六.6 的执行细则，改 AI 对话流或下载时必做）

### SSE（AI 对话流）

后端经 `data: {json}` 推 AgentScope 事件；前端 `shared/sse/SSEMessageBuilder.ts` 归一化为 `phase`（真相源），`api/sse.ts` dispatch 回调分发。

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 事件分派 | 读 `SSEMessageBuilder.ts`（phase 真相源）+ `api/sse.ts` dispatch + `useSSE` 各回调 | 每个 phase 组（`reply_*` / `model_call_*` / `thinking_*` / `text_*` / `data_*` / `tool_call_*` / `tool_result_*` / `hint` / `require_confirm` / `confirm_result` 等，完整清单以 SSEMessageBuilder.ts 为准）有消费分支；未知 phase 经可选链忽略不抛 | 只处理 `text_delta`，thinking/tool_call 内容落空 |
| 2 | 停止生成 | abort 路径 + `_detached` / `_streamGen` stale 检查 | 停止仅断流，已生成 rounds/content 保留；旧流回调失效不写屏 | 停止即清空输入与回复；旧流迟到事件污染新对话 |
| 3 | 折叠规则 | `ThinkingBlock` / `ToolCallCard` 折叠状态 | 各块折叠状态独立、初始态一致（见 `frontend/AGENTS.md` §3 SSE） | 嵌套折叠串状态；默认展开 |
| 4 | 终端事件 | `reply_end` / `exceed_max_iters` 分支 | 两者都触发 `onDone` + status `done`；未到终端即断流报错（`REPLY_END` 前关闭） | 只认 `reply_end`，超限流永不结束 |

### 文件下载（FileResponse / 导出）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | 通道选择 | 找报告下载/导出调用 | FileResponse 走 `fetch().text()`（或 blob），不套 JSON `api()` 信封解包 | 用 `api()` 解包二进制 → 乱码 |
| 2 | 错误分支 | catch / status | 非 2xx 读 text 并提示用户；不静默吞错 | 下载失败无任何提示 |

## WebSocket（六.7 的执行细则，改 WS 消费/推送时必做）

| # | 检查项 | 怎么扫 | 通过标准 | 常见反例 |
|---|--------|--------|----------|----------|
| 1 | URL 构建 | 找 `new WebSocket` / `wsUrl` 调用 | 一律 `wsUrl('/ws/...')` 经 Vite 代理 | 直连 `:8766` 或硬拼完整 URL |
| 2 | 事件覆盖 | 对照 `useTaskWebSocket.ts` switch ↔ 后端 `apps/test_runner/callbacks.py` | `/ws/test-run/{id}` 9 种 type（`log` / `heartbeat` / `case_started` / `step_started` / `step_result` / `iteration_result` / `case_finished` / `run_finished` / `device_error`）全覆盖；后端另发 `run_started`（前端暂不消费，消费时须同步 frontend/AGENTS.md） | 缺 `heartbeat` / `step_started` 分支 |
| 3 | 编辑广播 | `case-editing` 消费侧 | `/ws/case-editing/{id}` 收到 `case_updated` 触发刷新/锁提示 | 收到不处理 |
| 4 | 断线重连 | 重连钩子 + `_wsJustReconnected` | 重连后 `stepStates` 重置逻辑生效，无僵尸进度/重复首步 | 重连后 stepStates 未清，进度错位 |

## 改动验证（改后如何验证）

| 改动类型 | 验证方式 |
|---------|---------|
| 新增/修改 API 调用 | `curl` 往返验证 → 确认 `{status, data}` 结构 |
| 改 api.js | 登录 → 刷新 → 不跳回登录页（401 拦截器正常） |
| 改 WS URL | DevTools Network → WS → 状态码 101，持续收到帧 |
| 改报告下载 | 确认用 `fetch().text()` 而非 `api()`（FileResponse 非 JSON） |
| 改 router/routes | 点侧边栏每个菜单 → 确认加载 |
| 改 LoginView | 登录 → 跳转 dashboard |
| 改 SSE 事件处理 | 发一条消息 → 流式回复正常 → 思考块可折叠 → ToolCard 有结果 |
| 改停止生成 | 发送消息 → 中途点停止 → 已生成内容保留 |
| 改消息渲染 | 发多条消息 → 确认 Markdown 渲染正确（代码块/表格/列表） |
| 新增 fetch 页面 | 断网 → 刷新 → ErrorState + 重试 → 恢复 |
| 新增列表组件 | 空 DB → EmptyState（非空白）；有数据 → 正常 |
| 改 CSS/布局 | 构建 → 浏览器 → 缩小窗口确认可滚动 |
| 改 localStorage | 检查 key 格式统一 |

## 常见断裂点（诊断线索）

| 问题 | 前端表现 | 原因 |
|------|---------|------|
| 后端改了 JSON 字段名 | 页面空白，无报错 | `data.xxx` 为 undefined |
| `api()` 拿到非 JSON | 解析异常 | 后端返回了 HTML/纯文本 |
| WS type 不匹配 | 日志不更新 | switch 未命中 |
| 请求体字段名不一致 | `{status:false, message:...}` | snake_case vs camelCase |

## 新模块检查清单（新建 modules/{name}/ 时逐项打勾）

```
[ ] 5 个文件齐全: index.vue + api.js + routes.js + components/ + composables/
[ ] router.js 已注册（1 行 import + 1 行 spread）
[ ] AppSidebar.vue 已注册菜单项
[ ] index.vue 含 ErrorState + EmptyState + v-loading 三态
[ ] WorkbenchHeader 的 icon-gradient 使用模块色 var(--c-xxx)
[ ] 无独立 .css 文件、无 Pinia store（workflow 除外）
```

## 最终验证（所有改动必走）

```
[ ] 构建通过  cd frontend && npx vite build --mode development
[ ] 浏览器验证实际页面（非原型 HTML）
[ ] grep 残留色值   grep -rnP "color:\s*#[0-9a-fA-F]" src/modules/ --include="*.vue" | grep -v tokens
[ ] grep 残留旧类名（如果有删旧 CSS）
[ ] 文件未超上限  find src/modules/ -name "*.vue" | xargs wc -l | sort -rn | head -5
[ ] 自评 3 问：
      1. 删这个模块，其他模块不受影响？
      2. 改这个颜色，全局生效（从令牌取）？
      3. diff 里每一行都能追溯到用户的需求？
```

## 组件规格验收（Doodle Craft 主题，原 DESIGN_SYSTEM.md 已归档并入）

### 基础组件（Element Plus）

| 组件 | 规格 |
|------|------|
| Button | 圆角 `--app-radius-sm`、边框 2px solid `var(--ink)`、hover `--app-highlight`、一个操作区最多一个 primary |
| Table | 无外框、行间虚线分隔、表头暖色渐变、斑马纹、hover 浅 teal |
| Dialog | 遮罩无模糊、标题下划线分隔、内容无内部滚动 |
| Input | focus 边框 `--app-highlight`、错误边框 `--app-status-danger` |
| Tag/Badge | 圆角 3px 6px、边框 1.5px、状态色背景/文字 |

### 业务组件

| 组件 | 规格 |
|------|------|
| 拍立得卡片 | 图钉装饰、hover 归正放大、阴影 `--app-shadow-md` |
| 纸艺卡片 | 比拍立得更扁、无图钉、阴影 `--app-shadow-sm` |
| KPI 卡 | 顶部菱形色块 + 底部 `~` 水印、数字手写体 |
| 状态 Badge | 状态色正确、圆角 3px 6px |
| 筛选标签 | active 白底墨边、default 透明 |

### 三态 / 图标 / 动画

- 空态（居中图标 +「暂无数据」）/ 加载（骨架屏，非全屏 spinner）/ 错误（提示 +「重试」）
- 图标统一 Element Plus Icon，尺寸 14/16/20px，颜色 `currentColor`
- 动画只在 hover / 展开收起 / 路由切换，无布局抖动 / 数据更新动画
