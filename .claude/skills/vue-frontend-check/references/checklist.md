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
| 6 | Dialog/Drawer/Overlay | 长文案 + 矮视口 | 内容可滚；主按钮可达 | 错误卡无 max-height |
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
| 2 | DRF 通道 | HTTP 出口 | api→djangoClient→/api | 直连 :8765 |
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

见 [calibration.md](calibration.md) §7；另可：

```bash
rg -n "overflow|el-dialog|el-drawer" path/to/
rg -n "show-overflow-tooltip|ConfirmButton|locked" path/to/
rg -n "clear-case|refresh-tree" path/to/
rg -n "_meta|toRaw\(|config_json" path/to/
```
