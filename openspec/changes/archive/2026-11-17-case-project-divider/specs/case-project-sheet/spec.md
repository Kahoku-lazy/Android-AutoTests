## ADDED Requirements

### Requirement: 项目列表的分区虚线

用例项目列表页的「新建项目」操作带与下方内容（项目卡片网格或空态）之间 MUST 有一条**分区虚线**把两者分开。该虚线 MUST 由共享件 `SectionDivider` 提供（`1.5px dashed`、墨色 38%），MUST NOT 在页面里就地手写 `dashed`，也 MUST NOT 复用卡片自身的虚线边框充当分隔。虚线 MUST 只做分区，MUST NOT 承载文字或可点元素。

间距 MUST 不对称：操作带底部到虚线 MUST 小于虚线到内容的距离（当前 8px 对 16px），使分隔线读起来属于上方的操作带。虚线 MUST 与内容区同宽，MUST NOT 溢出内容区。空态与有卡片时 MUST 都插入该虚线，版式在两态之间保持一致。

#### Scenario: 有项目卡片时有分区线

- **WHEN** 打开 `/cases` 且存在至少一个项目
- **THEN** 「新建项目」与卡片网格之间出现一条浅墨虚线
- **AND** 该虚线宽度与内容区一致，且不可点击

#### Scenario: 空态时同样分隔

- **WHEN** 打开 `/cases` 且没有任何项目
- **THEN** 「新建项目」与空态之间同样有这条虚线

#### Scenario: 间距上紧下松

- **WHEN** 测量操作带底部到虚线的距离与虚线到内容的距离
- **THEN** 前者小于后者（约 24px 对 32px，含页面骨架的纵向 gap）
