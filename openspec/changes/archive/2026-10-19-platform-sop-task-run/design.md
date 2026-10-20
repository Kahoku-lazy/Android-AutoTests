## Context

控制设备任务今天由 `task_runner` 经 `engines.ai` 的规划 / 执行 / 验收工作流跑完。`engines/agents` 已能按 YAML 启动 SOP，但只从命令行读文件，模型写在环境变量里。任务附件是 `AITask` 上的一份 Markdown 文本加一个文件名，解析在 `attachments.py`，用 python-docx 与 PyMuPDF。同设备排队已在 `dispatch_device`：同一 `serial` 至多一条 running。上传目录的清理已是 7 天，且只删除该目录第一层文件。动机见 proposal.md。

## Goals / Non-Goals

**Goals:**

- 控制设备任务的启动与关闭都落到 `engines/agents` 的 SOP。
- 提交时由后端完成扩展名、YAML 格式和文档解析；智能体只拿到 YAML 路径、开场说明和文档 Markdown。
- 一份任务一份 YAML、多份文档；csv / json 在界面上可见但不可选。
- 关闭运行中的任务后，同一设备的下一条 pending 被拉起。

**Non-Goals:**

- 不删除 `engines/ai`，也不改 `planner_eval` / `model_test` 的规划评测入口。
- 不实现 csv、json 配置，也不新增第二个智能体。
- 不改平台任务线路的「线路开发中」占位。
- 不改手工命令行入口对旧 YAML（没有 `agent` 字段）的跑法：缺 `agent` 时仍按 `sop` 跑完全部用例，且不因前一条失败而停掉后一条。

## Decisions

### 1. 校验函数放在引擎，解析留在后端

YAML 结构检查做成 `engines/agents` 里的纯函数：读文件或读文本，返回成功或可读失败原因，不启动模型。平台路径上 `agent` 可以不写，未写时记为 `sop`；写了则全文件必须相同且等于 `sop`。后端创建任务时调用它。执行前对即将使用的文件再调用同一次函数，成功写入「配置加载成功」，失败写入「加载失败」并结束任务。

文档解析只在 `apps/ai_assistant/attachments.py`。`.md` 按 UTF-8 读入；`.docx` 与 `.pdf` 用 MarkItDown 转成 Markdown。引擎不依赖 MarkItDown。

备选：两套校验分别写在后端和引擎。会在「提交能过、启动失败」上漂移，否决。

### 2. 平台用独立入口跑 YAML，不改手工入口的失败后续跑

平台入口接收 YAML 路径、开场说明（任务目标 + 设备序列号 + 按上传顺序拼接的文档 Markdown），以及后端注入的执行 / 验收模型。它不接收工具清单。它按文件顺序跑用例，某条用例的运行阶段不是完成时，不再开始后面的用例。手工入口 `run_workflow` 保持现有循环。

执行前的那次检查失败时，平台入口直接返回，不装配 SOP。

### 3. 附件用子表，旧字段只服务历史任务

新增 `ai_task_attachments`：任务外键、种类（config / document）、文件名、正文、排序、原始文件相对路径。YAML 正文与文档 Markdown 都在这张表。`AITask.attachment` 与 `attachment_filename` 不再写入新任务；详情和列表对旧行仍读这两个字段。

列表返回文件名数组。卡片展示这些名字，不带正文。重新执行按排序复制子表行，不复制磁盘原件。

备选：把多份附件塞进现有 TextField。文件名、种类和加载结论无法分开，否决。

### 4. 原件放在现有上传目录的第一层

原始文件以扁平文件名写入 `MEDIA_ROOT`，沿用 `cleanup_upload_dir` 的 7 天删除。不建子目录，因为现有清理不递归。启动时若相对路径已不存在，用表中正文写成临时文件再交给智能体，用完删除临时文件。

### 5. 关闭使用新终态 cancelled

`TaskStatus` 增加 `cancelled`。`BaseRole` 已没有 `interrupt`。运行中任务的关闭改为取消正在跑的 SOP 事件流，不调用角色基类的中断方法。事件流退出后不再开始下一步或下一条用例，然后把任务写成 cancelled 并调用现有 `dispatch_device`。pending 拒绝关闭。失败卡的「重新执行」不出现在 cancelled 上。

进程重启时，遗留 running 仍按现有规则标为 failed。cancelled 不在重启时改写。

### 6. 控制设备任务不再装配规划工作流

`task_runner` 对控制设备任务改为调用平台 SOP 入口。`build_planner_user_input` 不再为新任务产生详情区块；历史任务详情在仍有该文本时按原样展示。

新建任务弹窗的助手下拉与平台小助手卡片共用同一份展示列表。当前该列表只有控制设备线路。只有一条时默认选中，未选择不能提交。提交带上该线路键，后端只接受这条已展示的线路。模型用所选线路上已配置的执行 / 验收模型，由后端注入给本次运行的角色，不读 `role/agents.py` 里的环境变量单例。

### 7. 工具只来自引擎代码

执行与验收的工具只由 `engines/agents/tools_config.py` 和 `engines/agents/tools/tool_*.py` 装配。平台 SOP 入口没有工具参数。后端不得把 `apps/ai_assistant/tools.py` 的清单传入，也不得按装配台「交给助手」增删这次 SOP 的工具。该清单仍只服务工具调试台。

备选：启动时由后端传入工具子集。这会让 Agent 的工具随平台配置变化，与「工具写在引擎代码里」相反，否决。

## 模块防火墙自检

- 写任务、附件和状态只经 `apps/ai_assistant/api.py`。View 只接收上传并调用 api。
- 引擎不 import `apps.*` 或 `django.*`。后端只调用 `engines.agents` 的校验函数与平台 SOP 入口，不向入口传递工具清单。
- 不新增跨 App 的 service / runner 导入。设备 serial 仍用本 App 已有的解析与 `dispatch_device`。
- 前端只走现有任务接口，不直连数据库。

## Risks / Trade-offs

- [关闭发生在模型正在调用工具时，当前步骤要等事件流退出] → 关闭请求取消该 SOP 的 asyncio 事件流，并把任务标为 cancelled。不调用 `BaseRole.interrupt`。后续步骤与下一条用例不再开始。详情保留已写出的步骤记录。
- [MarkItDown 对扫描版 PDF 抽不出文字] → 与现在一样拒绝创建任务并返回可读错误。
- [旧任务只有单附件字段] → 列表与详情先读子表，子表为空时回退旧字段。不回填历史行。
- [用例文件没有 `agent`] → 平台与手工入口都缺省为 `sop`。平台若写了其它名称则拒绝创建。助手改在新建任务弹窗选择，不写进 YAML。

## Migration Plan

1. 加附件子表与 `cancelled` 状态。旧任务不迁移正文。
2. 先接提交校验、解析和详情展示，执行仍可暂时不切，直到平台 SOP 入口能报告加载结论。
3. `task_runner` 改调平台 SOP 入口后，新的控制设备任务不再进入 `engines.ai` 工作流。
4. 回滚：恢复 `task_runner` 的旧调用，并让提交重新只收单份 Word/PDF。子表可留空，不删历史任务。

## Open Questions

无。提交时的两处默认（一份 YAML 内多条用例按序跑完；一次任务只收一份 YAML）已写入规格。
