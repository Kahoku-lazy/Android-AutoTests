## Purpose

让已登录用户用一张一次性凭证打开助手 HTML 报告，避免把登录令牌放进地址，也不把报告读成无法加载相对字体的 blob。

## ADDED Requirements

### Requirement: 查看前换一张一次性开门凭证

系统 SHALL 提供换票接口。已登录用户只能为本人可见、且已结束的一轮换票。ticket MUST 只绑定该对话栏与该报告编号，MUST NOT 包含磁盘路径。进行中的一轮 MUST NOT 发票。ticket 默认 60 秒内有效；这 60 秒是开门时间，不是阅读时间。

#### Scenario: 已完成的一轮可以换票

- **WHEN** 已登录用户为某栏一轮已完成的报告请求 ticket
- **THEN** 返回一张 60 秒内有效的 ticket
- **AND** 响应不含磁盘路径

#### Scenario: 进行中不发票

- **WHEN** 该轮仍在写入
- **THEN** 换票被拒绝
- **AND** 不返回 ticket

### Requirement: 凭证只开一次门

带 ticket 打开报告时，系统 MUST 不要求登录头。ticket 匹配该栏与该报告、且未过期、且未使用时，MUST 返回 HTML。打开成功后该 ticket MUST 立即作废。过期、已使用、栏或报告不匹配时 MUST 拒绝。报告加载完成后，用户可以继续阅读，不受 60 秒限制。再次打开 MUST 重新换票。

#### Scenario: 第一次打开成功且凭证作废

- **WHEN** 用户在 60 秒内用该 ticket 打开报告
- **THEN** 浏览器得到 HTML
- **AND** 同一 ticket 再次打开被拒绝

#### Scenario: 过期不能开门

- **WHEN** ticket 已超过 60 秒仍未使用
- **THEN** 打开被拒绝
- **AND** 不返回报告内容
