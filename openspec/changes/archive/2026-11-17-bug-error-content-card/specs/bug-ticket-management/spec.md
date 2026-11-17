## ADDED Requirements

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
