# bug-ticket-management Specification

## Purpose
把任务清单里的执行错误集中成可追溯、可分类、可处理的 BUG 台账：每张单保留来源任务编号，并能直接回答工作流哪一步出错、原因、期望结果与实际结果。

## Requirements

### Requirement: BUG 单分类与任务关联

系统 SHALL 为每张 BUG 单持久化分类、标题、错误正文、处理状态、来源任务编号、任务标题快照、任务类型、Agent 编号与创建人。分类 MUST 只有 `ui_automation`（UI 自动化）与 `case_authoring`（测试用例编写）两种，并 MUST 由来源任务的 `task_kind` 映射：`device_control` → `ui_automation`，`case_authoring` → `case_authoring`。每张 BUG 单 MUST 带非空 `task_id`，并 MUST 提供稳定的 BUG 编号用于展示。

#### Scenario: UI 自动化任务生成 UI 自动化 BUG
- **WHEN** 一个 `task_kind=device_control` 的任务进入失败终态
- **THEN** 生成的 BUG 单分类为 `ui_automation`
- **AND** BUG 单的 `task_id` 等于该任务编号，任务标题快照等于该任务标题

#### Scenario: 用例编写任务生成用例编写问题
- **WHEN** 一个 `task_kind=case_authoring` 的任务验收未通过
- **THEN** 生成的 BUG 单分类为 `case_authoring`
- **AND** BUG 单的 `task_id` 等于该任务编号

#### Scenario: BUG 编号稳定且可读
- **WHEN** 用户打开 BUG 单列表或详情
- **THEN** 每张 BUG 单显示形如 `BUG-0001` 的编号
- **AND** 同一张 BUG 单在列表、详情与刷新后编号不变

### Requirement: 任务错误自动登记为 BUG 单

系统 SHALL 在任务终态落库后自动登记 BUG 单。当前工作流任务（`assistant_sop`）状态为 `failed` 或 `interrupted` 时 MUST 只登记一张任务级 BUG 单，MUST NOT 按 `Task.result.failed` 中的步骤名或用例标题再拆多张。该单 MUST 保存失败步骤快照：至少包含序号、步骤名、期望结果、实际结果、尝试次数与原因类别。多个步骤没通过时 MUST 全部写入同一张单，标题 MUST 使用第一个失败步骤名。

历史 `device_control` 任务状态为 `failed` 且没有失败步骤快照时，MUST 继续按 `Task.result.failed` 中的每个失败用例各登记一张；该列表为空时 MUST 登记一张任务级 BUG 单。`interrupted` 且没有失败步骤快照时 MUST 登记一张任务级 BUG 单。用例编写任务状态为 `failed` 时 MUST 登记一张任务级 BUG 单；任务为 `completed` 但 `Task.result.case_import.status=failed` 时 MUST 登记一张入库失败 BUG 单。

`cancelled` 任务 MUST NOT 登记。登记失败 MUST NOT 改变任务状态、任务结果或验收结论。登记 MUST NOT 回读 HTML 报告或已删除任务来补全失败步骤。

#### Scenario: 工作流多步失败只登记一张

- **WHEN** 一条 `assistant_sop` 任务失败，且结果里有两个没通过的步骤
- **THEN** BUG 台账只新增一张关联该任务的 BUG 单
- **AND** 标题含第一个失败步骤名
- **AND** 该单同时保存两个步骤的序号、步骤名、期望结果、实际结果与尝试次数

#### Scenario: 抛错仍能看出停在哪一类

- **WHEN** 一条运行中的工作流任务因模型拒绝结束，且终态里没有已完成的步骤结论
- **THEN** 新增一张 BUG 单
- **AND** 失败步骤的原因类别为模型拒绝
- **AND** 实际结果是给人读的短句，不是网关原文或堆栈

#### Scenario: 中断任务登记

- **WHEN** 任务因进程退出被标记为 `interrupted`
- **THEN** 新增一张对应分类的 BUG 单
- **AND** 失败步骤写明中断原因
- **AND** 正文不出现「服务重启」

#### Scenario: 多个失败用例逐条登记

- **WHEN** 一条没有失败步骤快照的 UI 自动化任务失败，且 `result.failed` 包含两个用例标题
- **THEN** BUG 台账新增两张 `ui_automation` BUG 单，分别对应用例标题
- **AND** 两张 BUG 单都关联同一个任务编号

#### Scenario: 没有失败用例明细时登记任务级 BUG

- **WHEN** 一条没有失败步骤快照的 UI 自动化任务进入 `failed` 且 `result.failed` 为空
- **THEN** 新增一张任务级 `ui_automation` BUG 单，正文包含任务结果中的原因

#### Scenario: 用例入库失败登记

- **WHEN** 用例编写任务为 `completed` 且 `case_import.status=failed`
- **THEN** 新增一张 `case_authoring` BUG 单，正文包含入库失败原因
- **AND** 任务仍保持 `completed`，验收结论不变

#### Scenario: 取消任务不登记

- **WHEN** 任务被用户取消并进入 `cancelled`
- **THEN** BUG 台账不新增该任务的 BUG 单

### Requirement: BUG 登记幂等且尊重处理状态

同一任务、同一分类、同一来源键的 BUG 单 MUST 唯一。重复执行自动登记或历史同步 MUST NOT 新增重复记录；已存在的 BUG 单 MAY 更新标题、正文与任务快照，但 MUST NOT 覆盖用户已设置的处理状态 `open` / `resolved` / `ignored`。处理状态为 `resolved` 时 MUST 记录解决时间；状态回退为非 `resolved` 时 MUST 清空解决时间。

#### Scenario: 重复同步不翻倍
- **WHEN** 对同一批失败任务连续执行两次历史同步
- **THEN** 第二次不新增任何 BUG 单
- **AND** 第二次返回的 `created` 计数为 0

#### Scenario: 已解决状态不被同步覆盖
- **WHEN** 用户把一张 BUG 单改为 `resolved` 后再次同步来源任务
- **THEN** 该 BUG 单仍为 `resolved`
- **AND** 解决时间保持不变

#### Scenario: 重新打开清空解决时间
- **WHEN** 用户把一张已解决 BUG 单改回 `open`
- **THEN** 状态变为 `open`
- **AND** 解决时间被清空

### Requirement: BUG 单查询、详情与处理

系统 SHALL 提供 BUG 单列表、详情与处理状态更新能力。列表 MUST 支持按分类、处理状态与关键字过滤，关键字 MUST 匹配 BUG 标题、错误正文、任务标题与任务编号；列表 MUST 返回总数、分类计数、待处理计数与当前过滤结果。详情 MUST 返回完整错误正文与来源任务信息。列表与详情 MUST 只包含当前用户可见 Agent 产生的 BUG 单，MUST NOT 跨用户泄露。处理状态 MUST 只允许 `open`、`resolved`、`ignored`。

#### Scenario: 按分类查看
- **WHEN** 用户选择「UI 自动化」分类
- **THEN** 列表只返回 `ui_automation` BUG 单
- **AND** 选择「测试用例编写」时只返回 `case_authoring` BUG 单

#### Scenario: 按任务编号检索
- **WHEN** 用户在关键字框输入任务编号
- **THEN** 列表返回来源任务编号匹配的 BUG 单

#### Scenario: 非法状态被拒绝
- **WHEN** 客户端把 BUG 单状态改为 `open` / `resolved` / `ignored` 之外的值
- **THEN** 接口返回 400，BUG 单状态保持不变

#### Scenario: 不可见 Agent 的 BUG 不出现
- **WHEN** 当前用户看不到某个 Agent
- **THEN** 该 Agent 任务产生的 BUG 单不出现在列表、统计与详情中

### Requirement: 历史任务错误可补录

系统 SHALL 提供历史同步能力，扫描当前用户可见任务中处于 `failed` / `interrupted` 的任务，以及 `completed` 但用例入库失败的任务，按自动登记规则补录 BUG 单。同步 MUST 幂等，并 MUST 返回扫描数、新增数、更新数与跳过数。对已有失败步骤快照的当前工作流任务，同步 MUST 补进同一张任务级 BUG 单，MUST NOT 再按旧的用例来源键拆出新单。已按用例拆开的历史 BUG 单 MUST 保持原样。

#### Scenario: 同步历史失败任务

- **WHEN** 用户点击「同步历史错误」，且存在带失败步骤快照的历史失败任务
- **THEN** 该任务只对应一张任务级 BUG 单
- **AND** 响应包含扫描数、新增数与更新数

#### Scenario: 已拆开的历史单不被合并

- **WHEN** 同一任务下已经存在按用例拆开的 BUG 单，且任务结果里没有失败步骤快照
- **THEN** 再次同步不删除、不合并这些历史单

#### Scenario: 没有历史错误
- **WHEN** 当前用户可见任务中没有可登记的错误
- **THEN** 同步成功返回，新增数为 0，不创建空 BUG 单

### Requirement: BUG 列表的列头图标与首列身份单元

BUG 单列表的列头 MUST 呈现「图标 + 纯文字列名」，图标 SHALL 来自列配置，SHALL NOT 拼接进列名文本。首列 MUST 是一个身份单元：图标圆 + `BUG 编号`（主行）+ 创建时间（副行）；因此系统 SHALL NOT 再单列「创建时间」，同一时间信息 MUST NOT 在表格里出现两次。表格 MUST NOT 绘制列分隔线（`AppTable` 的 `border` MUST 为关闭），行分隔与表头分栏仍由既有表纸皮肤承担。分类、状态与操作列 MUST 保持原有语义与点击行为。关联任务列 MUST 只展示任务编号，MUST NOT 链到 `/tasks/:id`。

#### Scenario: 列头显示图标与纯文字列名

- **WHEN** 用户打开 `/bugs`
- **THEN** 六个列头各自渲染一个图标与其纯文字列名
- **AND** 列名文本本身不含图标字符

#### Scenario: 首列同时给出编号与创建时间

- **WHEN** 查看任一 BUG 行的首列
- **THEN** 该单元同时呈现图标圆、`BUG-xxxx` 编号与创建时间
- **AND** 表格中不存在独立的「创建时间」列

#### Scenario: 表格不画列线

- **WHEN** 检查 BUG 表格的结构与计算样式
- **THEN** `AppTable` 未开启 `border`，不出现竖直列分隔线
- **AND** 行与行之间仍可凭行底色与既有行分隔区分

#### Scenario: 原有交互不变

- **WHEN** 点击「查看」
- **THEN** 打开详情抽屉
- **AND** 点击按键不会同时触发行点击以外的副作用

#### Scenario: 列表不链到已下线的任务详情

- **WHEN** 查看关联任务列
- **THEN** 能看到来源任务编号
- **AND** 该列不存在指向 `/tasks/:id` 的链接

### Requirement: BUG 列表控制区排布与控件皮肤

BUG 列表的分类筛选（全部 BUG / UI 自动化 / 测试用例编写）MUST 与搜索框、「状态」下拉处于**同一行**，且分类筛选 MUST 位于搜索框左侧。分类筛选的文案字号 MUST 与「同步历史错误」相同（14px）。搜索框与状态下拉 MUST 采用已登记的 `Sketched UI Kit` 皮肤（虚线描边、无影），且 MUST NOT 再带字段标题文案——用途由占位提示表达。「同步历史错误」MUST 是**紫色渐变填充**键（墨色实边 + 位移硬影），位置 MUST 在「上一页 / 下一页」右侧的同一行右端。「上一页 / 下一页」MUST 也是**填充态**：可点击时为**浅绿填充**（`--app-status-success-bg`）配墨色实边与位移硬影，不可点击时 MUST 换成**灰填充**并撤除位移硬影，两态在视觉上一眼可分。分页文案与两个翻页键 MUST **常驻显示**，含只有 1 页或 0 条时；此时两键同时置灰仍可见，SHALL NOT 整组隐藏。工具条（显示行数、分页文案、翻页键）三项的字号 MUST 与翻页键一致（14px），工具条与表格之间的下边距 MUST 不小于 16px。页面 MUST NOT 再出现「共 N 张 BUG 单」这类与分页计数重复的提示文案。

#### Scenario: 分类筛选在搜索框左侧且同一行

- **WHEN** 打开 `/bugs`
- **THEN** 分类三枚 chip 位于搜索框左侧，与搜索、状态、同步键在同一行内
- **AND** 窗口变窄时该行整体换行，不发生控件重叠

#### Scenario: 输入控件是手稿皮肤

- **WHEN** 测量搜索框与状态下拉的计算样式
- **THEN** 两者描边为 `dashed`、`box-shadow` 为 `none`
- **AND** 两者上方没有「搜索」「状态」这类字段标题文字
- **AND** 同一页表格内的「查看」按键仍是实线主线皮肤（未挂 kit 作用域）

#### Scenario: 按钮的位置与两态

- **WHEN** 查看「同步历史错误」与翻页键
- **THEN** 「同步历史错误」是紫色渐变填充 + 墨色实边 + 位移硬影，且位于翻页键右侧的同一行右端
- **AND** 「上一页 / 下一页」可点击时为浅绿填充 + 墨色实边 + 位移硬影；不可点击时为灰填充且无位移硬影

#### Scenario: 工具条字号与间距统一

- **WHEN** 比较「显示行数」「第 X / Y 页 · 共 N 条」「上一页 / 下一页」与分类 chip 的文字字号
- **THEN** 这几处字号一致（14px）
- **AND** 工具条与表格之间的垂直间距不小于 16px

#### Scenario: 重复计数文案已移除

- **WHEN** 检查控制区文本
- **THEN** 不存在「共 N 张 BUG 单」
- **AND** 条数仍可从分页文案「第 X / Y 页 · 共 N 条」读到

### Requirement: BUG 分布环形图的中心文字居中于圆心

BUG 分布环形图的中心数字 MUST 以圆心为竖直与水平锚点居中；其下方「BUG 总数」标签 MUST 紧随数字之下。中心文字的竖直位置 MUST 用像素锚点（由图表固定高度推导），SHALL NOT 使用百分比 `top` 逐段摆放——百分比会随容器高度漂移并使数字偏上。

#### Scenario: 数字正对圆心

- **WHEN** 打开 `/bugs` 并量测环形图
- **THEN** 中心数字字形盒的竖直中心与圆环中心相差不超过 2px
- **AND** 「BUG 总数」标签位于数字下方，不与数字重叠

#### Scenario: 高度变化不漂移

- **WHEN** 图表容器按 `BUG_DISTRIBUTION_HEIGHT` 恒定高度渲染
- **THEN** 中心文字的 `top` 为像素数值而非百分比
- **AND** 圆心 `center` 与文字横向锚点同源（同为 `26%`）

### Requirement: BUG 表格的留白与可读字号

BUG 表格 MUST 与所在分区边缘留出间距（左右不贴边），数据行单元格内边距 MUST 不小于 16px，表头单元格 MUST 不小于 12px×16px。表纸底色 MUST 是**天蓝纵向渐变**：顶部约 10%、底部约 5% 的 `--c-workflow` 与纸色混合，且渐变 MUST 施加在表纸容器上、单元格保持透明——SHALL NOT 逐格着色（会形成一节一节的横向条纹）。表格正文 MUST 使用不小于 14px 的字号：分类、关联任务、状态与操作列「查看」键的文案 MUST 统一为 14px；首列编号与**标题**列 MUST 以 16px 呈现，**表头** MUST 同为 16px，创建时间副行 MUST 不小于 12px。行高 MUST 足以让两行首列内容不互相挤压。

#### Scenario: 表格不贴边且有内边距

- **WHEN** 检查 BUG 表格与其容器
- **THEN** 表格左右与分区边缘之间存在可见间距
- **AND** 每个数据单元格的上下内边距不小于 16px

#### Scenario: 首列两行可读

- **WHEN** 查看任一 BUG 行首列
- **THEN** 编号字号为 16px、时间字号不低于 12px，两行不重叠且行高容纳得下

#### Scenario: 列内字号分两档

- **WHEN** 比较同一行的标题、分类、关联任务、状态与「查看」键
- **THEN** 标题、表头与首列编号同为 16px
- **AND** 分类、关联任务、状态与「查看」均为 14px

#### Scenario: 表纸是连续渐变而非逐格着色

- **WHEN** 截取 BUG 表格首行与末行的单元格底色并比较
- **THEN** 首行比末行更深的棕黄，渐变沿表格纵向连续变化
- **AND** 同一行内相邻单元格底色一致，不出现横向分段

### Requirement: BUG 单详情错误内容卡

BUG 单详情里「错误内容」小节下的正文块 MUST 呈现为一张卡，而不是与元信息同色的浅底文本块。卡 MUST 具备：描边 `1.5px solid var(--app-border-strong)`、圆角 `--app-radius-md`（`6px 10px`）、硬偏移影 `4px 4px 0 0 var(--ink)`（模糊半径恒为 0）。卡底色 MUST 为 135° 斜向红色渐变，由 `--comp-bug-error-fill` 提供：标记红 `--color-red-69` 浓度自 18% 过渡到 6%，两端 MUST 由 `color-mix` 派生，MUST NOT 新增颜色原子或写字面量色值。卡内文字 MUST 为 14px（`--app-size-sm`）等宽字体，MUST NOT 小于 14px。同一抽屉里的元信息块与处理按键 MUST NOT 因本要求改变底色或字号。长内容 MUST 在卡内滚动（`max-height: 46vh`），MUST NOT 撑高抽屉。

#### Scenario: 错误内容是一张卡

- **WHEN** 打开任一 BUG 单详情
- **THEN** 「错误内容」下的正文块有可见描边、`6px 10px` 圆角与 4px 硬偏移影
- **AND** 其底色是从左上到右下的浅红渐变，与上方元信息块明显不同

#### Scenario: 卡内正文 14px

- **WHEN** 测量错误内容卡内的文字
- **THEN** 计算字号为 14px、字族为等宽字体

#### Scenario: 长内容在卡内滚动

- **WHEN** 错误内容超过抽屉可视高度
- **THEN** 卡片高度不超过 `46vh`，内容在卡片内部滚动
- **AND** 卡片自身的硬影不被滚动容器裁掉

#### Scenario: 元信息与按键不受影响

- **WHEN** 比较错误内容卡与上方元信息块、两个处理按键
- **THEN** 元信息块仍是无影浅底、按键样式与字号不变

### Requirement: BUG 单详情抽屉的字号分档

BUG 单详情抽屉内的字号 MUST 只取两档：**16px** 与 **14px**。以下元素 MUST 为 16px（`--app-size-md`）：`BUG-0066` 编号、单据标题、「错误内容」这类小节标题。以下元素 MUST 为 14px（`--app-size-sm`）：头部行的分类标签与状态标签、元信息块（关联任务 / 任务状态 / 创建时间 / 解决时间）、错误正文。抽屉标题「BUG 单详情」MUST 保持 16px，处理按键（标记已解决 / 忽略 / 重新打开）的字号 MUST NOT 因本要求改变。抽屉内 MUST NOT 出现 12px 及以下的正文或标签字号，也 MUST NOT 出现大于 16px 的标题字号。

#### Scenario: 编号与标签分档

- **WHEN** 打开任一 BUG 单详情
- **THEN** `BUG-0066` 编号的计算字号为 16px
- **AND** 分类标签与状态标签的计算字号均为 14px

#### Scenario: 标签不抢编号

- **WHEN** 并排比较头部行的编号与两个标签
- **THEN** 标签字号小于编号
- **AND** 标签仍带 `1.5px` 描边与 `2px 8px` 内边距，未被压成纯文字

#### Scenario: 标题与小标题同档

- **WHEN** 比较单据标题与「错误内容」小节标题
- **THEN** 两者计算字号均为 16px
- **AND** 不再出现 24px 的标题

#### Scenario: 其余回到 14px

- **WHEN** 测量元信息块（dt / dd）、任务链接与错误正文
- **THEN** 四者的计算字号均为 14px
- **AND** 错误正文不小于元信息块字号

#### Scenario: 按键字号不受影响

- **WHEN** 测量「标记已解决」「忽略」「重新打开」三个按键
- **THEN** 字号仍为按键自身规格（14px），未被正文档位改写

### Requirement: 错误内容行首标签加粗

BUG 单详情「错误内容」卡里的每一行 MUST 按「行首标签 + 值」渲染：行首标签（含冒号原文，如 `来源任务：`）MUST 以 `font-weight: var(--app-font-weight-bold)`（700）呈现，冒号之后的值 MUST 保持常规字重；两者 MUST 同为 14px 等宽字体，字号 MUST NOT 因加粗而改变。

标签识别 MUST 走模块内纯函数（`helpers/errorDetail.ts::splitErrorDetail`），MUST NOT 在组件里写解析逻辑。判定规则 MUST 为：行首连续不超过 12 个字符 + 一个中文或英文冒号，且该段 MUST NOT 含空白与斜杠；冒号后紧跟 `//` 的行 MUST 整行当正文（避免把 URL 协议段当标签）。没有行首标签的行（堆栈、缩进片段、纯文本）MUST 整行当正文，MUST 保留原有前导空白与折行行为。加粗 MUST NOT 改变卡片底色、描边、硬影与行高。

#### Scenario: 字段名与值字重不同

- **WHEN** 打开详情里带 `来源任务：#227 …`、`任务状态：failed` 的 BUG 单
- **THEN** 每行冒号及其之前的字段名计算字重为 700
- **AND** 冒号之后的值为常规字重（400），字号同为 14px

#### Scenario: 堆栈行不被当标签

- **WHEN** 详情含 `  at run (runner.js:12)` 这类行
- **THEN** 该行整行按正文渲染，前导空格保留
- **AND** 行内不出现加粗片段

#### Scenario: URL 不被拆成标签

- **WHEN** 详情含 `https://example.com/a:b`
- **THEN** 整行按正文渲染，不把 `https:` 摘出来加粗

#### Scenario: 卡片几何与行高不变

- **WHEN** 比较加粗前后的错误内容卡
- **THEN** 底色渐变、1.5px 描边、4px 硬影与行距一致
- **AND** 长内容仍在卡内滚动

### Requirement: BUG 单抄录用例身份

自动登记 BUG 单时，系统 MUST 把来源任务的用例展示文案和行列表抄进该 BUG 单。展示文案 MUST 与任务清单使用同一规则：一条为标题，多条为「第一条标题 · 共 N 条」，里程碑为「里程碑」，没有身份为空。BUG 单标题 MUST 继续使用失败步骤名或失败类别，MUST NOT 改成用例标题。来源键 MUST 继续由任务、分类与既有来源键决定，MUST NOT 把用例标题写入来源键。任务后来被删除时，BUG 单上的文案和行列表 MUST 仍然可读。没有用例身份的任务所登记的 BUG 单，这两项 MUST 为空。重复登记 MAY 更新这两项，但 MUST NOT 覆盖人工处理状态。

#### Scenario: 失败单带上同一句用例文案

- **WHEN** 一条冻结了三条用例的工作流任务因步骤未通过而登记 BUG 单
- **THEN** BUG 单标题仍含第一个失败步骤名
- **AND** 用例展示文案为「第一条标题 · 共 3 条」
- **AND** 详情按顺序给出三条「项目名 / 标题」

#### Scenario: 用例改名不拆出第二张单

- **WHEN** 同一任务再次登记，且用例库中的标题已经改变
- **THEN** 不新增 BUG 单
- **AND** 原单的用例展示文案保持首次抄录的内容

#### Scenario: 旧任务的 BUG 单不编造用例

- **WHEN** 一条没有用例身份的历史任务被登记为 BUG 单
- **THEN** 该单的用例展示文案和行列表都为空

### Requirement: BUG 关键字可搜用例身份

BUG 列表关键字 MUST 额外匹配用例展示文案。匹配用例文案时 MUST 返回该 BUG 单，MUST NOT 要求正文里重复出现同一标题才可搜到。既有的标题、正文、任务标题、任务编号与 BUG 编号匹配 MUST 保持不变。

#### Scenario: 按用例标题搜到 BUG 单

- **WHEN** 用户输入某张 BUG 单抄录的用例标题，且该标题不在 BUG 标题中
- **THEN** 列表返回该 BUG 单

### Requirement: BUG 单保存失败步骤四问

系统 SHALL 为带失败步骤快照的 BUG 单持久化每一步的序号、步骤名、期望结果、实际结果、尝试次数与原因类别。原因类别 MUST 只取：步骤未通过、模型拒绝、设备命令失败、平台错误、已中断。期望结果 MUST 是该步必须达成的结果；没有该文本时 MUST 明确写「未记录」，MUST NOT 留空。实际结果 MUST 是给人读的短句。列表与详情 MUST 返回该快照；没有快照的旧单 MUST 返回空列表，MUST NOT 因此报错。

#### Scenario: 详情能读出四问

- **WHEN** 打开一张由步骤未通过产生的 BUG 单详情
- **THEN** 能读到出错步骤的序号与名称、原因类别「步骤未通过」、期望结果与实际结果
- **AND** 能读到该步的尝试次数

#### Scenario: 旧单没有快照

- **WHEN** 打开一张登记于本能力之前、没有失败步骤快照的 BUG 单
- **THEN** 详情仍返回原来的错误正文
- **AND** 失败步骤列表为空

### Requirement: BUG 单详情按四问展示

带失败步骤快照的详情 MUST 按「出错步骤、原因类别、期望结果、实际结果」展示，MUST NOT 只把快照拼成一段不可分的纯文本。第一个失败步骤 MUST 展开；其余失败步骤 MUST 可展开查看，且默认不占满抽屉。没有快照的旧单 MUST 继续展示原来的错误正文。详情字号仍 MUST 只取 16px 与 14px 两档。错误内容区 MUST 保持既有卡片几何：描边、圆角、硬偏移影与卡内滚动。

#### Scenario: 四问分栏可读

- **WHEN** 打开一张带失败步骤快照的 BUG 单
- **THEN** 页面分别呈现出错步骤、原因类别、期望结果与实际结果
- **AND** 用户不必阅读整段原文才能回答这四问

#### Scenario: 其余失败步骤默认折叠

- **WHEN** 一张单含两个失败步骤
- **THEN** 第一个步骤的四问直接可见
- **AND** 第二个步骤需展开后才显示期望与实际

#### Scenario: 旧单退回原文

- **WHEN** 打开一张没有失败步骤快照的 BUG 单
- **THEN** 详情仍显示原来的错误正文
- **AND** 不出现空白的四问卡

### Requirement: 有报告才提供查看入口

BUG 单详情在来源任务仍有 HTML 报告定位时 MUST 提供「查看报告」，并 MUST 打开该任务已生成的 HTML 报告。没有报告定位，或来源任务已删除时，MUST 只显示任务编号，MUST NOT 链到 `/tasks/:id`，也 MUST NOT 显示不可用的报告按钮。报告入口 MUST NOT 把报告正文复制进 BUG 单。

#### Scenario: 有报告时可以打开

- **WHEN** 打开一张来源任务仍有报告定位的 BUG 单并点击「查看报告」
- **THEN** 打开该任务的 HTML 报告
- **AND** 页面不导航到 `/tasks/:id`

#### Scenario: 没有报告时不给死链

- **WHEN** 打开一张没有报告定位的 BUG 单
- **THEN** 仍能看到来源任务编号
- **AND** 不出现「查看报告」
- **AND** 不存在指向 `/tasks/:id` 的链接
