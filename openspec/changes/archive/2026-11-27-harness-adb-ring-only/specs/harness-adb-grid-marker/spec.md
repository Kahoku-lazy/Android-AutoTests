## ADDED Requirements

### Requirement: 候选点标记只用环点形态

截屏候选点工具 SHALL 接受 `marker` 参数，缺省 `ring`。所有候选点 MUST 画成空心圆环，圆环 MUST NOT 完全覆盖目标——目标轮廓 SHALL 能从环心透出。工具 MUST NOT 绘制十字准星。`marker="cross"` MUST 被视为已废弃别名并按 `ring` 渲染，MUST NOT 因此报错；其它取值 MUST 返回可读错误。

#### Scenario: 不传形态时就是环点

- **WHEN** 调用方不传 `marker`
- **THEN** 图上每个候选点是空心圆环，没有任何十字

#### Scenario: 旧调用传十字也画环

- **WHEN** 调用方仍传 `marker="cross"`（旧提示词/旧任务）
- **THEN** 图上仍只出现空心圆环，调用不报错

#### Scenario: 环点不遮住目标

- **WHEN** 以缺省形态在 49 px 见方的目标上取 5×5 候选点
- **THEN** 压中目标的点表现为空心圆环，目标轮廓在环心可见

## MODIFIED Requirements

### Requirement: 环点阵以行列轴标注代替逐点序号

环点形态 MUST NOT 给每个候选点写序号，SHALL 在点阵外沿标注行号与列号：列号标在首行上方、行号标在首列左侧。标注 MUST 在贴近画面边缘时向内收，MUST NOT 被画布裁掉。

#### Scenario: 行列号只出现一次

- **WHEN** 取 5×5 候选点
- **THEN** 首行上方恰好有一组 1~5 的列号，首列左侧恰好有一组 1~5 的行号，每个候选点旁没有序号

#### Scenario: 贴边不裁切

- **WHEN** 点阵中心靠近屏幕顶部
- **THEN** 列号标注整体向下收进画面内，仍然可读

### Requirement: 点数与参数校验

工具的每边点数 SHALL 只接受 3、5、7；两轴步长 MUST 为正（y 方向允许 0 表示沿用 x 步长）；`marker` 取值非法时 MUST 返回可读错误而不是抛未处理异常。单次绘制的候选点上限 MUST 为 49 个，超出时 MUST 返回可读错误。

#### Scenario: 非法形态

- **WHEN** 调用方传 `marker="dot"`
- **THEN** 返回带可读错误的 JSON，`status` 为 false，且不产生截图

#### Scenario: 点数上限

- **WHEN** 取 7×7 候选点
- **THEN** 49 个点全部绘制成功；换成 9×9 的请求时被参数校验拒绝

## REMOVED Requirements

### Requirement: 候选点标记支持十字与环点两种形态

**Reason**: 十字臂与目标同宽，会遮住小控件；实际运行中模型按提示词持续选择十字，环点阵能力未被采用。改用环点阵作为唯一形态。

**Migration**: `marker="cross"` 保留为废弃别名，收到时按 `ring` 渲染，调用不报错；新提示词只提环点阵。
