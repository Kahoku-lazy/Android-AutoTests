# device-text-input Specification

## Purpose
定义平台向 Android 设备输入文本的对外行为：ASCII 走键入快路径，Unicode 经设备输入法提交，并保证输入法的安装、恢复与失败语义可预测、可测试。

## Requirements

### Requirement: ASCII 文本走键入快路径
纯 ASCII 文本 SHALL 通过设备系统键入命令提交；系统 MUST NOT 为这类输入切换设备默认输入法，以保证速度与对现有行为零影响。

#### Scenario: 输入英文与数字
- **WHEN** 向聚焦输入框输入 `hello world 123`
- **THEN** 文本完整出现在输入框
- **AND** 设备默认输入法与调用前一致

### Requirement: Unicode 文本经输入法提交
含非 ASCII 字符的文本 SHALL 经设备输入法提交，MUST 支持中文、emoji 与中英混排；输入框最终内容 MUST 与原文逐字一致。

#### Scenario: 输入中文
- **WHEN** 向聚焦输入框输入 `中文验证`
- **THEN** 输入框内容为 `中文验证`，无丢字或乱码

#### Scenario: 输入 emoji 与中英混排
- **WHEN** 向聚焦输入框输入 `测试😸ABC`
- **THEN** 输入框内容为 `测试😸ABC`

### Requirement: 输入法准备与安装分工
平台 SHALL 在任务开始前确保目标设备已安装并启用所需输入法；未安装时 SHALL 按固定版本自动安装。文本输入工具本身 MUST NOT 下载或写入文件；设备未安装时 MUST 返回可读错误并给出安装命令。安装包 MUST 经过大小与 SHA-256 校验，MUST 支持用本地同版本文件离线安装。

#### Scenario: 任务开始自动预装
- **WHEN** 目标任务设备未安装输入法
- **THEN** 平台在任务开始前完成安装与启用
- **AND** 该任务后续的中文输入成功

#### Scenario: 工具遇到未装设备
- **WHEN** 直接调用文本输入工具，且目标设备未安装输入法
- **THEN** 返回失败与可执行的安装命令
- **AND** 输入框没有新增任何文本

#### Scenario: 安装包不可用
- **WHEN** 下载失败、校验不通过或设备拒绝安装
- **THEN** 任务开始处记录可读警告，不阻塞不需要文本输入的任务
- **AND** 后续中文输入返回失败与原因，输入框没有新增文本

### Requirement: 输入法恢复
无论输入成功、失败或中途异常，系统 MUST 在操作结束后恢复调用前的默认输入法；恢复失败 MUST 记录可诊断信息，MUST NOT 掩盖输入结果。

#### Scenario: 输入成功后恢复
- **WHEN** 一次中文输入完成
- **THEN** 设备默认输入法恢复为调用前的值

#### Scenario: 输入失败后恢复
- **WHEN** 中文输入过程中广播失败
- **THEN** 设备默认输入法仍恢复为调用前的值

### Requirement: 可靠清空
要求先清空时，进入输入法通道的调用 MUST 通过输入法提供的清空能力清除已聚焦输入框内容；ASCII 快路径 MAY 沿用按键清空，MUST NOT 依赖对输入框无效的按键事件。

#### Scenario: 清空后输入
- **WHEN** 输入框已有旧文本，调用方要求先清空再输入新文本
- **THEN** 输入框最终只包含新文本

### Requirement: 长文本分片
超过单次提交上限的文本 SHALL 分片提交；分片 MUST 按字符边界切分，MUST NOT 拆坏多字节字符；拼接结果 MUST 与原文一致。

#### Scenario: 超长中文
- **WHEN** 输入一段超过单次提交上限的中文
- **THEN** 输入框读回内容与原文完全一致

### Requirement: 失败不静默降级
输入法不可用、广播失败或超时时，系统 SHALL 以失败返回并说明原因；MUST NOT 退回 ASCII 键入命令，造成静默截断、乱码或看似成功。

#### Scenario: 广播失败
- **WHEN** 输入法广播返回失败
- **THEN** 调用方收到失败结果与可读原因
- **AND** 输入框没有新增文本

### Requirement: 既有契约不变
工具名、入参（文本、设备序列号、是否先清空）与 JSON 返回形状 MUST NOT 变化；不涉及 Unicode 的调用行为 MUST 与变更前一致。

#### Scenario: 旧调用方式
- **WHEN** 按变更前的方式输入 ASCII 文本
- **THEN** 返回结构与字段含义保持不变

### Requirement: 多设备隔离
指定设备序列号时，安装输入法、切换输入法与提交文本 MUST 只作用于该设备；MUST NOT 改变其他设备的默认输入法或前台状态。

#### Scenario: 两台设备同时连接
- **WHEN** 对其中一台执行中文输入
- **THEN** 另一台设备的默认输入法保持不变
