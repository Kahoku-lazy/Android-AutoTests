## 1. 任务附件与关闭状态

- [x] 1.1 新增 `ai_task_attachments`（种类、文件名、正文、排序、原件相对路径）与 `TaskStatus.cancelled`，并生成迁移。验证：`python manage.py check` 通过，`python manage.py makemigrations ai_assistant --check` 无未生成迁移。
- [x] 1.2 在 `apps/ai_assistant/api.py` 增加附件写入、按任务读取、重新执行时复制附件行。View 与 runner 不直接写该表。验证：`python -m pytest tests/graybox/unit/test_ai_task_attachments.py -q` 覆盖创建、排序读取与复制。

## 2. SOP 校验与平台入口

- [x] 2.1 在 `engines/agents` 增加 YAML 纯函数校验：用例列表、每条 `agent`/`title`/`steps`、每步非空 `action`/`assert`、全文件只有一个 `agent` 且必须是 `sop`。手工入口在缺少 `agent` 时仍按 `sop` 跑。验证：`python -m pytest tests/graybox/unit/test_sop_case_file.py -q` 覆盖合法文件、缺字段、两个智能体、手工缺省 `sop`。
- [x] 2.2 增加平台 SOP 入口：接收 YAML 路径、开场说明与后端注入的模型；不接收工具清单，工具只按 `tools_config.py` 装配。执行前再校验并返回「配置加载成功」或「加载失败」；多条用例按序执行，前一条未完成则不开始后一条。不调用 MarkItDown，不读环境变量单例。验证：`python -m pytest tests/graybox/unit/test_sop_platform_entry.py -q` 用替身角色覆盖加载失败、两条用例的顺序、第一条失败时第二条未启动，以及入口不接受工具参数。

## 3. 提交、解析与详情

- [x] 3.1 文档解析改为：`.md` 按 UTF-8 读入，`.docx` 与 `.pdf` 经 MarkItDown 转为 Markdown；依赖写入 `requirements.txt`。验证：`python -m pytest tests/graybox/unit/test_task_attachment_parse.py -q` 覆盖这三种扩展名与解析失败。
- [x] 3.2 新建任务提交：后端拒绝 csv、json、第二份 YAML 和缺少 YAML；通过时把原件以扁平文件写入现有上传目录，正文写入附件表。验证：`python -m pytest tests/graybox/unit/test_task_publish_attachments.py -q`。
- [x] 3.3 列表返回全部文件名且不含正文；详情返回每份文档 Markdown、YAML 正文与加载结论；没有新附件行的历史任务回退旧的单附件字段。新任务详情不再返回规划输入。验证：`python -m pytest tests/graybox/unit/test_task_attachment_detail.py -q`。
- [x] 3.4 原件超过 7 天仍由现有上传清理删除；原件已不在时，启动用表中正文写成临时文件再交给平台入口，用完删除。验证：`python -m pytest tests/graybox/unit/test_task_attachment_retention.py -q`。

## 4. 启动、关闭与排队

- [x] 4.1 `task_runner` 对控制设备任务改为调用平台 SOP 入口，模型取控制设备线路配置，不传入 `apps/ai_assistant/tools.py` 的工具清单，并把加载结论写回任务。验证：`python -m pytest tests/graybox/unit/test_task_runner_sop.py -q` 确认不再调用 `engines.ai` 的规划工作流，且调用参数中没有工具清单。
- [x] 4.2 运行中任务可关闭：取消正在跑的 SOP 事件流，不调用 `BaseRole.interrupt`。状态改为 cancelled，并经 `dispatch_device` 拉起同设备最早的 pending。pending 拒绝关闭。cancelled 不提供重新执行。验证：`python -m pytest tests/graybox/unit/test_ai_task_device_dispatch.py tests/graybox/unit/test_task_cancel.py -q`。

## 5. 新建任务界面

- [x] 5.1 新建任务弹窗分成配置与文档。配置列出 csv、yaml、json，csv 与 json 标明「暂不可用」且不能选择；文档可多份，扩展名为 md、docx、pdf。标题、目标、设备下拉保持不变。验证：改动的 Vue 文件通过 `npm run build`，并按 vue-frontend-check 门禁核对上传区没有硬编码色和小于 12px 的字号。
- [x] 5.2 任务卡片展示全部附件名；详情展示加载结论与文档 Markdown，新任务不展示「送给规划模型的输入」；运行中任务提供关闭，失败任务仍可重新执行。验证：同上，`npm run build` 通过，并核对关闭只出现在 running 卡片上。

## 6. 关单核对

- [x] 6.1 对改动的后端路径执行 `ruff check` 与 `ruff format --check`。验证：两条命令退出码为 0。
- [x] 6.2 确认任务写库只出现在 `apps/ai_assistant/api.py`，引擎文件无 `apps.` 或 `django.` 导入。验证：`python tools/gen_arch_stats.py --check-boundaries` 退出码为 0。

## 7. 助手在新建任务弹窗选择

- [x] 7.1 平台 YAML 允许不写 `agent`，未写时按 `sop`；写了非 `sop` 或两个不同 `agent` 仍拒绝。验证：`python -m pytest tests/graybox/unit/test_sop_case_file.py -q`。
- [x] 7.2 新建任务弹窗增加助手下拉，选项与平台小助手卡片同源，只有一条时默认选中且必选。提交携带线路键，后端只接受当前展示的 `device_control`。验证：`python -m pytest tests/graybox/unit/test_task_assistant_choice.py -q`，以及 `npm run build`。
