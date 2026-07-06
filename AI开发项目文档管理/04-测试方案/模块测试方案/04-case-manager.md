# 模块测试方案 — 用例工程

> 关联子PRD：`02-PRD需求/子PRD/03-case-manager.md` · 版本：v2.0 · 日期：2026-07-06
> 上线版本 v1.0（2026-06-30）→ v2.0 新增：目录树管理、IoT PRD 字段、步骤调试、批量操作、卡片/列表双视图
> 自动化脚本：`tests/functional/case-manager/run_tests.py` · 用例规格：`tests/functional/case-manager/test_spec.md`

---

## 1. 测试范围

| 类型 | 内容 | 端点/组件 |
|------|------|----------|
| 接口测试 | 12 个 REST API | `/api/cases/*` |
| 前端页面 | 主列表页 + 用例编辑页 | `index.vue`, `CaseEditor.vue` |
| 前端组件 | 目录树、用例卡片、步骤编排器、步骤查看器 | `DirectoryTree`, `CaseCard`, `StepEditor`, `StepViewer` |
| 数据测试 | IoT PRD 字段、步骤 JSON 完整性、YAML 导出 |

### 页面清单

| 路由 | 组件 | 功能 |
|------|------|------|
| `/cases` | `index.vue` | 主列表页：目录树 + 卡片/列表双视图 + 用例详情面板 + YAML 导出 |
| `/cases/new` | `CaseEditor.vue` | 新建用例：基本信息 + 步骤编排 |
| `/cases/:id/edit` | `CaseEditor.vue` | 编辑用例：表单回填 + 脏数据追踪 + 路由守卫 |

### 自动化测试执行

```bash
# 全量 12 条（现有 Playwright 脚本）
python tests/functional/case-manager/run_tests.py

# 按维度筛选
python tests/functional/case-manager/run_tests.py --dim FUNC
python tests/functional/case-manager/run_tests.py --dim API
python tests/functional/case-manager/run_tests.py --dim DATA

# 单条执行
python tests/functional/case-manager/run_tests.py --case CASE-FUNC-01

# 查看报告
open tests/functional/case-manager/reports/report_latest.html
```

---

## 2. 目录管理测试

### 2.1 目录 CRUD

| 编号 | 用例 | 接口 | 预期 |
|:--:|------|------|------|
| CM-DIR-01 | 创建一级目录 | `POST /cases/directories/create` | 200，返回 `{ok:true, directory:{id,name,parent_id}}` |
| CM-DIR-02 | 创建二级子目录 | `POST /cases/directories/create` + `parent_id` | 200，子目录挂在父目录下 |
| CM-DIR-03 | 创建三级目录 | 同上，指定二级目录为 parent | 400，超过两级限制 |
| CM-DIR-04 | 同名目录冲突 | 同一 parent 下创建同名目录 | 400，名称重复 |
| CM-DIR-05 | 获取目录树 | `GET /cases/directories` | 200，树形结构含目录节点 + 用例叶子节点 |
| CM-DIR-06 | 重命名目录 | `POST /cases/directories/:id` + `{action:"update"}` | 200 |
| CM-DIR-07 | 删除空目录 | `POST /cases/directories/:id` + `{action:"delete"}` | 200 |
| CM-DIR-08 | 删除非空目录 | 目录下有子目录或用例时删除 | 409，提示先清空 |
| CM-DIR-09 | 批量移动 | `POST /cases/directories/batch-move` | 200，`{moved:N, errors:[]}` |

### 2.2 目录树前端交互

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-TREE-01 | 树节点点击过滤 | 点击目录节点 | 右侧用例列表按目录过滤，面包屑更新 |
| CM-TREE-02 | 面包屑恢复全部 | 点击面包屑「全部用例」 | 恢复全部用例列表 |
| CM-TREE-03 | 右键菜单 — 目录节点 | 右键目录 → 弹出菜单 | 显示：新建子目录 / 新建用例 / 重命名 / 删除 |
| CM-TREE-04 | 右键菜单 — 用例节点 | 右键树中用例 → 弹出菜单 | 显示：编辑用例 / 删除用例 |
| CM-TREE-05 | 右键 → 新建子目录 | 输入名称 → 确定 | 目录创建，树刷新 |
| CM-TREE-06 | 右键 → 从目录新建用例 | 点击「📋 新建用例」 | 跳转 `/cases/new?directory_id=X`，目录预选 |
| CM-TREE-07 | 长按拖拽移动 | 长按 500ms → 拖到目标目录 → 确认 | 移动成功，树刷新 |
| CM-TREE-08 | 批量选择模式 | 点击「☑ 选择」 | 树节点显示复选框 |
| CM-TREE-09 | 批量全选/取消 | 点击「全选」 | 全部勾选/取消 |
| CM-TREE-10 | 批量移动到目录 | 勾选 → 「📂 移动到...」→ 选目标目录 | 移动成功，退出选择模式 |
| CM-TREE-11 | 节点显示用例计数 | 目录节点 badge | `case_count` 与右侧列表一致 |
| CM-TREE-12 | 空目录状态 | 无目录时 | 显示「暂无目录，点击上方 + 按钮创建」 |
| CM-TREE-13 | 目录删除确认弹窗 | 点击删除 → 弹窗 | 包含「确认删除」+ 子项警告提示 |

---

## 3. 用例 CRUD 测试

### 3.1 API 测试

| 编号 | 用例 | 接口 | 预期 |
|:--:|------|------|------|
| CM-API-01 | 创建用例（含完整步骤） | `POST /cases/definitions` | 200，返回 `{ok:true, id:"TC-..."}` |
| CM-API-02 | 创建用例（空步骤 + IoT 字段） | `POST /cases/definitions` | 200，`priority`/`design_method`/`precondition`/`expected_result`/`metrics` 存入 |
| CM-API-03 | 创建用例（缺标题） | `POST /cases/definitions` + 空 title | 后端无校验。前端 `ElMessage.warning("请输入用例标题")` |
| CM-API-04 | TC-ID 自动生成 | 新建不传 id | 生成格式 `TC-YYYYMMDD-HHMMSS-XXXX` |
| CM-API-05 | 获取用例列表 | `GET /cases/definitions` | 200，`definitions` 数组 |
| CM-API-06 | 按目录过滤 | `GET /cases/definitions?directory_id=N` | 200，仅返回该目录及其子目录下的用例 |
| CM-API-07 | 获取单个用例 | `GET /cases/definitions/:id` | 200，含完整 `steps_data` JSON |
| CM-API-08 | 更新用例 | `POST /cases/definitions` (upsert，带已有 id) | 200，字段更新 |
| CM-API-09 | 启用/停用用例 | `POST /cases/definitions` + `enabled:false` | 200，`enabled` 切换 |
| CM-API-10 | 删除用例 | `DELETE /cases/definitions/:id` | 200，幂等（不存在的 ID 也返回 200） |
| CM-API-11 | 批量导入 | `POST /cases/definitions/batch` | 200，`{imported:[], skipped:[], failed:[]}` |
| CM-API-12 | 批量导入 + 指定目录 | 同上 + `directory_id` | 导入的用例归属目标目录 |
| CM-API-13 | 批量导入上限 | 单次 >500 条 | 后端限制，返回 400 + `"单次最多导入 500 条"` |
| CM-API-14 | 批量导入空数组 | `cases: []` | 200，`{imported:0, skipped:0, failed:0}` |

### 3.2 用例保存往返验证（API → DB → API）

| 编号 | 用例 | 步骤 | 预期 |
|:--:|------|------|------|
| CM-RT-01 | 完整字段往返 | POST 创建 → GET 回读 | 所有字段一致：title/category/package_name/priority/design_method/precondition/expected_result/metrics/steps_json |
| CM-RT-02 | steps_json 结构完整性 | 创建含 5 种步骤类型的用例 → GET 回读 | 每个步骤的 type/xpath/timeout 等字段无丢失 |
| CM-RT-03 | 更新后字段一致性 | POST 创建 → POST 更新 title → GET 回读 | title 已更新，其他字段不变 |
| CM-RT-04 | 目录归属变更 | POST 创建（无目录）→ POST 更新 directory_id → GET | 用例归属新目录 |

---

## 4. 17 种步骤类型验证

> 步骤类型定义于 `frontend/src/modules/case-manager/step-utils.js`，StepEditor 中 17 种类型分 4 组。

### 4.1 元素操作（3 种）

| 编号 | 步骤类型 | 必填字段 | 验证点 |
|:--:|------|------|------|
| CM-ST-01 | `click` | xpath | 选取元素 → XPath 填入 → 描述自动填充元素名称 |
| CM-ST-02 | `long_click` | xpath | 可选 timeout（长按秒数），默认 0.8s |
| CM-ST-03 | `click_indexed` | xpath, index | index 从 0 开始，点击第 N 个匹配元素 |

### 4.2 滑动操作（2 种）

| 编号 | 步骤类型 | 必填字段 | 验证点 |
|:--:|------|------|------|
| CM-ST-04 | `swipe` | direction, distance | 方向选 ↑↓←→，distance 50-3000px |
| CM-ST-05 | `drag` | xpath, direction, distance | 从元素位置向指定方向拖动 |

### 4.3 等待操作（5 种）

| 编号 | 步骤类型 | 必填字段 | 验证点 |
|:--:|------|------|------|
| CM-ST-06 | `wait` | xpath | 可选 timeout（默认 10s） |
| CM-ST-07 | `wait_disappear` | xpath | 可选 timeout |
| CM-ST-08 | `wait_any` | xpath, xpath2 | 两个 XPath 用 `\|` 分隔，任一出现即继续 |
| CM-ST-09 | `wait_toast` | expected_text | 等待系统 Toast 消息文本 |
| CM-ST-10 | `sleep` | timeout | 固定秒数暂停，无需设备 |

### 4.4 检查操作（2 种）

| 编号 | 步骤类型 | 必填字段 | 验证点 |
|:--:|------|------|------|
| CM-ST-11 | `verify_text` | xpath, expected_text | 校验元素文本等于预期值 |
| CM-ST-12 | `poll_text` | xpath, expected_text | 轮询直到文本变化为预期值 |

### 4.5 应用操作（5 种）

| 编号 | 步骤类型 | 必填字段 | 验证点 |
|:--:|------|------|------|
| CM-ST-13 | `start_app` | xpath（包名） | xpath 字段标签变为「包名」，自动填充用例 package_name |
| CM-ST-14 | `kill_app` | xpath（包名） | 同上，强制停止应用 |
| CM-ST-15 | `restart_app` | xpath（包名） | 先 kill → sleep(1s) → start |
| CM-ST-16 | `retry_click` | xpath, index | index 字段含义变为「最多重试次数」，点击后等待确认元素出现 |
| CM-ST-17 | `log` | description | 纯记录日志，无设备操作 |

> ⚠️ **v3 规划步骤**：`long_click`、`swipe`、`drag` 三种步骤前端 UI 已完整实现（可选、可编辑、可保存），但下游 test-runner 执行引擎（`adapter.py`）尚未实现对应的 uiautomator2 操作映射。执行时会被跳过并记录 `WARNING: step type not implemented`。测试方案中的步骤编辑器测试覆盖这三种类型的 **UI 交互**（类型选择、字段渲染、保存入库），但不覆盖 **实际设备执行**。详见子PRD §3.2.4。

### 4.6 步骤编辑器前端测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-SE-01 | 添加步骤 | 点击「添加步骤」 | 列表末尾新增默认 click 步骤，自动展开 |
| CM-SE-02 | 上限 100 步 | 已有 100 步时点击添加 | `ElMessage.warning("单用例最多 100 个步骤")` |
| CM-SE-03 | 删除步骤 | 点击删除 → 确认弹窗 → 确定 | 步骤移除，列表长度 -1 |
| CM-SE-04 | 删除不询问 | 勾选「本次编辑不再询问」→ 删除 | 后续删除跳过确认弹窗 |
| CM-SE-05 | 复制步骤 | 点击「📋」复制 | 当前步骤下方插入副本，自动展开 |
| CM-SE-06 | 拖拽排序 | 拖拽步骤到新位置 | 步骤顺序改变，视觉反馈（高亮+阴影） |
| CM-SE-07 | 切换步骤类型 | 步骤类型从 click → wait | 字段变化：xpath 保留，新增 timeout 可选字段 |
| CM-SE-08 | 切换为应用类步骤 | 类型切换为 start_app | xpath 自动填入用例包名 |
| CM-SE-09 | 展开/折叠步骤 | 点击步骤摘要栏 | 展开显示类型专属表单字段 |
| CM-SE-10 | 步骤摘要中文显示 | 不同类型显示不同摘要 | 如「👆 点击「登录按钮」」「⏳ 等待「LoadingSpinner」出现」 |
| CM-SE-11 | 元素选取器搜索 | 在 xpath 下拉框输入关键词搜索 | 过滤显示匹配元素，分组按页面 |
| CM-SE-12 | 选取元素后自动填充 | 从下拉选中一个元素 | xpath 填入，描述自动填入元素名称 |
| CM-SE-13 | 单步调试执行 | 选择设备 → 点击 ▶ 单步执行 | 发送 POST `/runner/run-step`，显示 ✅ 或 ❌ 结果 |
| CM-SE-14 | 从头执行全部 | 点击 ▶▶ 从头执行 | 顺序执行全部步骤，失败时弹窗询问继续/停止 |
| CM-SE-15 | 从当前位置执行 | 点击 ▶▶▸ | 从该步骤开始执行到末尾 |
| CM-SE-16 | 接收元素定位模块事件 | element-locator 发送 `add-step-to-case` | 自动添加 click 步骤，xpath + 描述已填 |

---

## 5. 用例编辑器测试

### 5.1 基本信息表单

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-ED-01 | 新建页面加载 | 导航到 `/cases/new` | 表单空，TC-ID 自动生成，保存/退出按钮可见 |
| CM-ED-02 | TC-ID 重新生成 | 新建页点击「重新生成」 | ID 变化，格式 `TC-YYYYMMDD-HHMMSS-XXXX` |
| CM-ED-03 | 编辑页面回填 | 导航到 `/cases/:id/edit` | 所有字段回填：id/title/category/package/priority/steps |
| CM-ED-04 | 编辑模式 ID 不可改 | 编辑页查看 ID 字段 | disabled 状态 |
| CM-ED-05 | 标题必填校验 | 标题空 → 点击保存 | `ElMessage.warning("请输入用例标题")` |
| CM-ED-06 | 包名必填校验 | package_name 空 → 点击保存 | `ElMessage.warning("请输入 APP 包名...")` |
| CM-ED-07 | 保存成功 | 填写标题+包名 → 保存 | `ElMessage.success("保存成功")`，新建页 URL 变为 `/cases/:id/edit` |
| CM-ED-08 | 保存失败 | 模拟服务器错误 | `ElMessage.error(data.error)` |
| CM-ED-09 | 优先级选择 | el-select 选 P0 | 表单 `priority` 更新为 `"P0"` |
| CM-ED-10 | 启用开关 | toggle el-switch | `enabled` 切换 true/false |

### 5.2 目录选择器

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-ED-11 | 级联选择目录 | el-cascader 展开选目录 | `form.directory_id` 绑定叶子节点 ID（`emitPath: false`） |
| CM-ED-12 | 新建时预选目录 | URL 带 `?directory_id=X` | cascader 默认选中对应目录 |
| CM-ED-13 | 清除目录选择 | cascader clearable 点击 ✕ | `directory_id` 设为 null |

### 5.3 IoT PRD 字段

| 编号 | 用例 | 条件 | 预期 |
|:--:|------|------|------|
| CM-ED-14 | PRD 字段默认隐藏 | 无 IoT 数据时 | design_method/precondition/expected_result/metrics 区域不渲染 |
| CM-ED-15 | PRD 字段条件显示 | 任一 IoT 字段有值 | 「PRD 导入字段」分隔区出现 |
| CM-ED-16 | 设计方法只读 | design_method 有值时 | el-input readonly，展示五法之一 |

### 5.4 脏数据追踪与路由守卫

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-ED-17 | 未修改离开不触发 | 编辑页无修改 → 点击退出 | 直接跳转 `/cases`，无弹窗 |
| CM-ED-18 | 修改后点击退出 | 编辑字段 → 点击「退出」 | 弹窗「未保存的修改...不保存直接退出？」 |
| CM-ED-19 | 修改后浏览器后退 | 编辑字段 → 浏览器后退 | `onBeforeRouteLeave` 拦截，弹窗确认 |
| CM-ED-20 | 修改后保存 → 离开 | 编辑 → 保存 → 退出 | 无弹窗，`initialForm` 已重置 |
| CM-ED-21 | 「去元素定位」先保存 | 点击「去元素定位」→ 未保存 | 自动调用 `save()`，成功后再跳转 `/elements` |

---

## 6. 用例列表页测试

### 6.1 双视图切换

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-LIST-01 | 默认卡片视图 | 首次访问 `/cases` | card-grid 可见，`viewMode === "card"` |
| CM-LIST-02 | 切换到列表视图 | 点击 📋 按钮 | 表格 `case-table` 可见 |
| CM-LIST-03 | 切换到卡片视图 | 点击 🃏 按钮 | card-grid 可见 |
| CM-LIST-04 | 视图偏好持久化 | 切换到列表 → 刷新页面 | localStorage 读取 `case-manager-view-mode`，保持列表视图 |
| CM-LIST-05 | 列表视图列 | 列表视图检查表头 | ID/标题/目录/分类/启用/操作 6 列 |
| CM-LIST-06 | 列表空状态 | 无数据时 | 显示「📋 暂无用例定义」+ 创建按钮 |

### 6.2 用例卡片

| 编号 | 用例 | 检查点 | 预期 |
|:--:|------|------|------|
| CM-CARD-01 | 卡片信息完整 | 检查卡片元素 | ID (monospace) / 优先级徽章 (P0 红/P1 黄/P2 灰) / 启用标签 / 标题 / 目录名 (青色) / 步骤数 |
| CM-CARD-02 | 启用/停用样式 | enabled: false 的用例 | Card color="brown"，无 teal 高亮 |
| CM-CARD-03 | 卡片点击查看详情 | 点击卡片主体 | `selectedCase` 赋值，右侧详情面板出现 |
| CM-CARD-04 | 编辑按钮 | 点击「编辑」 | 跳转 `/cases/:id/edit` |
| CM-CARD-05 | 删除按钮 | 点击「删除」→ 确认弹窗 → 确定 | `deleteDefinition()` → 列表刷新 |
| CM-CARD-06 | 删除取消 | 点击「删除」→ 取消 | 无变化 |

### 6.3 用例详情面板

| 编号 | 用例 | 检查点 | 预期 |
|:--:|------|------|------|
| CM-DETAIL-01 | 详情头部信息 | 选中用例后 | 显示：ID / 启用标签 / 优先级 / 标题 / 分类 / 目录名 / 包名 / 步骤数 |
| CM-DETAIL-02 | 步骤阅读器 | 详情面板下半部分 | StepViewer 渲染所有步骤，展开可看字段详情 |
| CM-DETAIL-03 | 从详情编辑 | 点击「📝 编辑用例」 | 跳转 `/cases/:id/edit` |
| CM-DETAIL-04 | 返回列表 | 点击「↩ 返回列表」 | `selectedCase` 清空，恢复用例列表 |

### 6.4 YAML 导出

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-YAML-01 | 导出 YAML | 点击「📤 导出 YAML」 | `ElMessage.success("YAML 已导出：xxx.yaml")` |
| CM-YAML-02 | 导出文件列表 | 导出后 | 文件列表面板出现，显示文件名/大小/时间 |
| CM-YAML-03 | 下载导出文件 | 点击「⬇ 下载」 | `window.open` 下载文件 |
| CM-YAML-04 | 收起飞导出面板 | 点击「✕ 收起」 | 面板隐藏 |
| CM-YAML-05 | 空文件列表 | 无导出时展开面板 | 显示「暂无导出文件」 |

---

## 7. 安全测试

| 编号 | 用例 | 操作 | 预期 |
|:--:|------|------|------|
| CM-SEC-01 | 未登录访问页面 | 清除 token → 访问 `/cases` | 重定向到 `/login` |
| CM-SEC-02 | 未登录访问编辑页 | 清除 token → 访问 `/cases/new` | 重定向到 `/login` |
| CM-SEC-03 | 无 token 调 API | 不带 Authorization header 调 `/api/cases/definitions` | 401 |
| CM-SEC-04 | 过期 token 调 API | 过期 JWT 调 API | 401，前端拦截器自动尝试刷新 |
| CM-SEC-05 | 删除确认弹窗 | 删除用例 | 必须经过 `ElMessageBox.confirm`，不可直接调用 |

---

## 8. 用例统计

| 分组 | 子项 | 数量 |
|------|------|:--:|
| 目录管理 API | CM-DIR-01 ~ 09 | 9 |
| 目录树前端 | CM-TREE-01 ~ 13 | 13 |
| 用例 CRUD API | CM-API-01 ~ 14 | 14 |
| CRUD 往返验证 | CM-RT-01 ~ 04 | 4 |
| 步骤类型验证 | CM-ST-01 ~ 17 | 17 |
| 步骤编辑器 | CM-SE-01 ~ 16 | 16 |
| 用例编辑器 | CM-ED-01 ~ 21 | 21 |
| 用例列表 | CM-LIST-01 ~ 06 | 6 |
| 用例卡片 | CM-CARD-01 ~ 06 | 6 |
| 用例详情 | CM-DETAIL-01 ~ 04 | 4 |
| YAML 导出 | CM-YAML-01 ~ 05 | 5 |
| 安全测试 | CM-SEC-01 ~ 05 | 5 |
| **总计** | | **120** |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-06-30 | 基于子PRD v1.0 输出，覆盖 10 API + 14 步骤类型 + 5 YAML + 5 UI |
| v2.0 | 2026-07-06 | 基于实际代码重写。新增：目录树管理 (22)、IoT PRD 字段、步骤编辑器 (16)、脏数据追踪 (5)、安全测试 (5)。步骤类型由 14 种扩展到 17 种（新增 long_click/swipe/drag，wait_either→wait_any）。总数 34→120 |
| v2.1 | 2026-07-06 | 基于子PRD v3.5 交叉审查 + functional-testing 规范对齐。标注 3 种 v3 规划步骤的执行状态，补批量导入空数组测试 (CM-API-14) |
