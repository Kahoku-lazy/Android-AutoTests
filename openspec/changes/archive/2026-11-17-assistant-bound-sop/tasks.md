## 1. 工作流记录

- [x] 1.1 在 `ai_assistant` 新增工作流模型：名称、执行 `assistant_id`、验收 `assistant_id`、创建与更新时间。不存提示词、模型参数和工具勾选。生成迁移。验证：`python manage.py makemigrations --check --dry-run` 无待生成，且模型字段不含 `system_prompt`。
- [x] 1.2 在 `ai_assistant.api` 增加创建与列表。名称为空、任一侧名片不存在时拒绝；两侧可以是同一编号。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -q -k workflow` 覆盖这三支。
- [x] 1.3 在同一 `api.py` 增加只读解析：返回两侧运行名、提示词正文、连接参数与工具勾选。名片或 Agent 配置缺失时给出可读错误。两侧显示名相同时，一侧运行名追加 `assistant_id`。验证：同一 pytest 范围断言不复制字段进工作流表，且改名片后再次解析得到新提示词。

## 2. 引擎装配

- [x] 2.1 在 `backend_bridge/workflow` 新增按绑定参数装配一对角色的函数。两次调用 `create_agent` 时只传提示词正文和连接参数，不传模型短名，不传提示词文件名。验证：`python -m pytest -c tests/pytest.ini tests/engines/backend_bridge/unit -q -k sop_roles` 断言新函数源码不含 `model_short` 与 `UI_EXECUTOR_PROMPT`。
- [x] 2.2 执行侧走 `select_tools`。验收侧只挂勾选与只读目录的交集，不改传入的勾选。未知工具名拒绝。验证：同一测试断言写工具不在验收实例上，且 `build_sop_roles` 的旧调用测试仍通过。
- [x] 2.3 新增运行函数：接收已解析的 `SopSpec`、一对绑定和可选 serial。有 serial 才追加现有开场模板；无 serial 不拒绝。取消、观测和报告目录沿用现有平台入口。验证：单测覆盖有 serial 与无 serial 两支，且不调用 `SPEC_KEYS`。

## 3. 新任务入口

- [x] 3.1 `TaskKind` 增加 `assistant_sop`。提交只接受一份里程碑 YAML，缺 `subject` 或 `description`、以及用例格式（`action` / `assert`）都拒绝。YAML 中的角色字段不覆盖工作流绑定。验证：`python -m pytest -c tests/pytest.ini tests/task -q -k assistant_sop` 覆盖接受与拒绝。
- [x] 3.2 `task_runner` 为新类型调用解析 API 与新运行函数。解析失败写成任务失败，不开始第一步。`device_control` 仍走 `run_sop_once`。验证：同一 pytest 范围用假解析断言失败路径不调用运行函数，且旧任务测试不改断言。
- [x] 3.3 运行详情保留本次使用的两个 `assistant_id` 与运行名。验证：任务详情序列化含这两个编号，且工作流表行数不因运行增加副本。

## 4. 按次计价

- [x] 4.1 逐次用量追加模型名。新运行函数传入「角色名 → 模型名」。旧记录没有该字段时，控制设备收尾不读它。验证：`python -m pytest -c tests/pytest.ini tests/engines -q -k usage` 断言新记录含模型名，旧收尾测试金额不变。
- [x] 4.2 新任务收尾按每次调用的模型名调用现有价目函数后相加。模型名缺失的该次记 0，并在结果中留可读说明。验证：`deepseek-flash` 与 `deepseek-v4-pro` 各一次的夹具，总费用等于两侧分别计价之和。
- [x] 4.3 确认 `device_control` 的整单计价函数入参与调用点未改。验证：`git diff -- backend/apps/task_list/task_runner.py` 中 `_price_costs` 的旧调用仍只传一个模型名。

## 5. 前端

- [x] 5.1 新增「新建 SOP」表单：名称、执行助手下拉、验收助手下拉。保存走新 API。不进入助手对话页。验证：`cd frontend && npx vitest run tests/ai-assistant` 覆盖两侧必选与同一名片可同时入选。
- [x] 5.2 新增运行入口：选择已有工作流并上传一份 YAML。设备控件可空。提交字段只有工作流编号、YAML 与可选 serial。验证：同一 vitest 范围断言空设备可以提交，且请求体不含提示词和工具清单。
- [x] 5.3 入口位置已由第 8 节改为卡片与弹窗；5.1 / 5.2 的字段与提交口径不变，只移动落点。

## 6. 边界与收口

- [x] 6.1 跑架构边界检查，确认 `task_list` 只经 `ai_assistant.api` 解析，`engines` 无 `django` / `apps` 导入。验证：`python utils/gen_arch_stats.py --check-boundaries` 通过。
- [x] 6.2 跑本变更相关后端与前端检查。验证：`python manage.py check`、相关路径 `ruff check`、`python -m pytest -c tests/pytest.ini tests/ai_assistant tests/task tests/engines/backend_bridge -q`、`cd frontend && npx vue-tsc --noEmit`。

## 7. 工作流编辑与删除

- [x] 7.1 `ai_assistant.api` 增加编辑与删除：编辑先算完字段再整幅回写三字段，校验失败不改任何字段；删除只删工作流行。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant -q -k workflow` 覆盖改名、换名片、缺名片拒绝后记录不变、删除后名片与任务仍在。
- [x] 7.2 路由增加 `PATCH` / `DELETE /api/ai/sop-workflows/{workflow_id}/`：不存在返回 404 与可读 message，名称为空与名片缺失返回 400 并说明是哪一侧。验证：`python -m pytest -c tests/pytest.ini tests/arch -q -k api_path` 路径可解析。

## 8. 前端分区卡片

- [x] 8.1 页面顺序改为助手网格在上、工作流网格在下；工作流不再是页内常驻表单，旧面板组件删除。验证：`cd frontend && npx vitest run tests/ai-assistant`。
- [x] 8.2 工作流卡片复用颜料片皮肤：名称 + 「执行助手 → 验收助手」+ 只有「配置 / 任务」两个动作；笔色取执行助手的 marker，缺执行助手回落 teal。验证：同一 vitest 范围断言卡片只有两个按钮，且不出现工具清单、模型名与编号。
- [x] 8.3 工作流区块新增「新建工作流」入口与配置弹窗：新建走 `POST`，编辑预填并走 `PATCH`，删除二次确认后走 `DELETE`；没有助手时弹窗拦住保存。验证：同一 vitest 范围覆盖新建必选、编辑预填与回写、删除确认。
- [x] 8.4 运行改为卡片上的任务弹窗：带入工作流编号，只提交 `workflow_id` / `config` / 可选 `device_serial`，空设备可提交，成功后关闭弹窗并提示任务编号。验证：同一 vitest 范围断言请求体字段与弹窗关闭。

## 9. 文档与自检

- [x] 9.1 把工作流形体登记回 doodle-craft 颜料片参考（同一组件两种形体），模块 `AGENTS.md` 补页面顺序与两个弹窗。
- [x] 9.2 跑 `python run.py check`、`cd frontend && npx vue-tsc --noEmit`、`node tests/check-style-gates.mjs`、`node tests/check-dashed-whitelist.mjs`；`npx openspec validate assistant-bound-sop --strict`。

## 10. 回归修复（提交入口）

- [x] 10.1 恢复 `POST /api/tasks/submit/` 路由：`TaskSubmitAPIView`、`TaskSubmitInputSerializer` 与前端调用都还在，但 `task_list/urls.py` 里 `path("submit/", ...)` 与它的 import 被任务清单重构一起删掉了，任务弹窗提交因此返回 404（前端兜底文案「目标不存在，请刷新页面后重试」）。验证：认证后提交不存在的工作流返回 400「工作流不存在」；`tests/arch/unit/test_api_path_callers.py` 的未解析路径从 15 条降到 12 条。

## 11. 设备改成下拉选择

- [x] 11.1 设备地址口径下沉到共享层：`shared/helpers/device-address.ts`（USB 出序列号、局域网出 `IP:端口`、别名记录不可选）与 `shared/api/devices.ts`（`GET /api/devices/`）；任务清单改为引用共享件，行为不变。验证：`cd frontend && npx vitest run tests/shared/p0/device-address.spec.ts tests/task-list`。
- [x] 11.2 任务弹窗把「设备序列号」输入框换成下拉：选项来自设备管理、含「不指定设备」空选项、不提供手填；设备列表取不到时只提示且仍可提交。验证：`npx vitest run tests/ai-assistant` 覆盖选项取值、别名记录不列、空设备提交、选中局域网设备提交 `IP:端口`。

## 12. 分区虚线与便签卡

- [x] 12.1 新增 `shared/components/SectionDivider.vue`（1.5px 浅墨虚线）分隔助手区与工作流区，并把它登记为虚线白名单第 6 个落点（doodle-craft SKILL 表格 + `check-dashed-whitelist.mjs` OWNERS + 模块 AGENTS）。两区间距由 24px 抬到 40px。验证：`node tests/check-dashed-whitelist.mjs` 通过且 OWNERS 计 6。
- [x] 12.2 工作流卡片改成 Tape Strip 便签卡：白卡 + 1.5px 浅墨虚线框 + 顶部半透明笔色渐变胶带 + 左对齐名称/「执行 → 验收」+ 底部「配置 / 任务」两枚文字按钮与一块纯色占位块（无交互）。胶带用同一支笔色的 `color-mix(..., transparent)` 竖向渐变，不写死颜色。验证：`npx vitest run tests/ai-assistant` 覆盖胶带、三个底部元素、占位块 `aria-hidden`；截图核对。
- [x] 12.3 便签卡放大并按需求定稿：网格列宽 200 → 260px、内距 24px、标题 20px；正文拆成三行（名称 / `执行者：…` / `验收者：…`）；底部三块统一「64×30 + 2px 墨框 + 2px 墨影」，`配置` 柠黄、`任务` 青绿，第三块用笔色浅底同尺寸占位。验证：同一 vitest 范围断言三行文案、两枚按钮的底色修饰类与占位块同排；截图核对尺寸。
- [x] 12.4 与 StyleKit Tape Strip 参考图对齐「配重」：虚线框 `1.5px/38%` → `2px/32%`；底排三块 `2px 墨框 + 2px 黑影 + 2px 圆角` → `1px/22% 描边 + 5px 圆角 + 静息无影`（hover 才出浅影），尺寸收到 `56×26`；填充压到 `配置 85%`、`任务 78%` 模块色（纸底比参考白底暖）；内距 24 → 32、元素间距 4 → 8、正文行高 `snug` → `normal`；胶带去描边、`88×26`、渐变 `42%→14%`；网格 `280–360px` 封顶。验证：截图与参考并排比对；`npx vitest run tests/ai-assistant`、`node tests/check-style-gates.mjs`、`npx vue-tsc --noEmit` 全通过。
