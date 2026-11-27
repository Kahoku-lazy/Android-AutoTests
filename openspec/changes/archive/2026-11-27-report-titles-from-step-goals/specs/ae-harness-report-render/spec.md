## MODIFIED Requirements

### Requirement: 两处标题栏用平台品牌字体渲染且不依赖外部文件

报告的侧栏品牌标题、页头品牌小标签与页头主标题 SHALL 使用平台品牌手写体（`Ziku FeiYang`），字体数据 MUST 随 HTML 内联（`@font-face` 的 `src` 为 data URI），使报告在 `blob:`、`file://` 与 HTTP 三种打开方式下呈现同一支字体。

报告正文（`--app-font`）SHALL 首选 `HarmonyOS Sans SC`，与平台 `--font-body` 同一支。字体 MAY 在文档来源为 `blob:` 或 `http(s):` 时按同源地址加载平台既有的 `/fonts/harmonyos-sans/harmonyos-sans.css`；MUST NOT 把鸿蒙字体文件内嵌进报告，MUST NOT 引用第三方字体域名。字体不可用时 MUST 回退到 `PingFang SC → Noto Sans SC → Microsoft YaHei → system-ui`，MUST NOT 因字体加载失败中断渲染。

#### Scenario: 前端以 blob: 打开报告

- **WHEN** 用户在前端「执行报告」页点击打开，正文以 `URL.createObjectURL(new Blob([content]))` 的 `blob:` 文档呈现
- **THEN** 侧栏 `AGENT可视化报告`、页头品牌小标签 `AGENT 执行报告` 与页头主标题 MUST 呈现品牌手写体
- **AND** 正文 MUST 以 `HarmonyOS Sans SC` 渲染，字体请求 MUST 只落在本报文来源的同源 `/fonts/harmonyos-sans/` 下

#### Scenario: 直接双击本地报告文件

- **WHEN** 用户用浏览器直接打开落盘的 `*.html`
- **THEN** 三处标题文字 MUST 呈现同一支品牌手写体，不回落为系统黑体
- **AND** 正文 MUST 回退到系统字体栈且页面不报错

#### Scenario: 同源字体不可用

- **WHEN** 平台字体文件 404 或被网络策略阻断
- **THEN** 报告正文回落系统字体，排版与功能不受影响
- **AND** 页面 MUST NOT 因字体加载失败抛错或白屏

## ADDED Requirements

### Requirement: 页头显示这份报告是谁的

报告页头 SHALL 由「品牌小标签 + 报告主标题」组成：品牌小标签固定为 `AGENT 执行报告`，主标题取记录里的报告标题。

报告标题 MUST 按来源取值：任务报告取任务标题，任务标题为空时取用例标题；助手报告取会话标题，会话标题为空时取助手名。两处都为空时，页头 MUST 退回改动前只有品牌标题的形态（24px 品牌手写体），MUST NOT 显示占位符或空的主标题。

主标题 MUST 单行呈现；超出页头可用宽度时 MUST 以省略号截断，并 MUST 通过 `title` 属性暴露完整文本。主标题文本 MUST 按 HTML 转义，MUST NOT 执行其中任何标记。

品牌小标签 MUST 使用 12px 字号，主标题 MUST 使用页头档位的 24px；两者 MUST 都取自品牌手写体。

#### Scenario: 任务报告显示任务标题

- **WHEN** 打开一份由任务产生的报告，任务标题为「H705F 音乐功能测试（UI 验证）」
- **THEN** 页头左侧显示 12px 的 `AGENT 执行报告`
- **AND** 其后显示 24px 主标题「H705F 音乐功能测试（UI 验证）」
- **AND** 通过状态与五个页签的位置与改动前一致

#### Scenario: 助手报告回退到助手名

- **WHEN** 打开一份助手会话报告，会话标题为空、助手名为「Android-UI-Executor」
- **THEN** 页头主标题显示「Android-UI-Executor」

#### Scenario: 没有标题的报告退回品牌标题

- **WHEN** 打开一份记录里既没有任务标题、也没有用例标题、也没有会话标题的报告
- **THEN** 页头显示改动前的 24px 品牌标题 `AGENT 执行报告`
- **AND** 页面不出现空标题行或 `None` 字样

#### Scenario: 超长标题单行省略

- **WHEN** 报告标题超过页头可用宽度
- **THEN** 主标题以省略号结尾且不换行、不挤压页签
- **AND** 鼠标悬停可看到完整标题

### Requirement: 报告区分组标题就是这一步的目标

报告区的子目标分组标题 MUST 是该步的目标（SOP 步骤的 `subject`），MUST NOT 再在标题里重复步骤序号——序号已由手绘徽标表达。

分组标题与徽标之间 MUST NOT 出现「第 N 步 · 」前缀；正文文本块里作为导航标记的 `### 目标：…` 行 MUST NOT 再渲染成标题或重复正文。

分组 MUST 按「第几步」归并，MUST NOT 按标题文字归并——两步目标同名时仍须是两个分组。

历史记录里的 `subject` 形如「用例标题 · 第 N 步」时，渲染 MUST 改用该步 `description` 里的「动作：」行作为标题（没有该行时才去掉后缀），MUST NOT 把同一序号显示两次，MUST NOT 让同一用例的多个步骤并成一个分组。

#### Scenario: 五个步骤显示五个不同目标

- **WHEN** 打开一份 5 步的 SOP 报告
- **THEN** 五个分组标题分别是这五步的目标，彼此不同
- **AND** 每个标题前只有一个手绘序号，标题内不含 `第 N 步`

#### Scenario: 旧记录不再重复序号

- **WHEN** 打开一份历史记录，其 `subject` 仍带「· 第 3 步」这样的后缀
- **THEN** 该分组标题只显示目标文本，不出现第二个「第 3 步」

#### Scenario: 模型的目标标记不再重复

- **WHEN** 某步执行者的第一段文本以 `### 目标：保存命名快照` 开头
- **THEN** 该行不再在文本卡里渲染成标题
- **AND** 页面上的步骤标题只出现一次「保存命名快照」
