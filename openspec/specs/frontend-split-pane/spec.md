# frontend-split-pane Specification

## Purpose
定义分栏台（左栏 + 右栏）的左右拖动分隔手柄契约：鼠标拖动改宽度、宽度夹取、键盘可达、双击复位、宽度持久化，以及窄屏下不渲染手柄。两个工作台（元素定位 / 用例管理）共用本契约，后续分栏页可复用同一件。

## Requirements

### Requirement: 分栏台提供可拖动的分隔手柄

分栏台 MUST 在左右两栏之间渲染一个分隔手柄，用户按住左键左右拖动时 MUST 实时改变左栏宽度。拖动过程中 MUST 有拖动光标（`col-resize`）与正文不可选的反馈；松手后 MUST 保持新宽度，并把该宽度**记住**——同一分栏台再次进入（含刷新页面）MUST 恢复该宽度。手柄 MUST NOT 在窄屏（两栏未并置）时渲染。

#### Scenario: 鼠标拖动改变左栏宽度

- **WHEN** 用户在分隔手柄上按住左键向右拖动 120px 后松手
- **THEN** 左栏宽度 MUST 比拖动前增加约 120px
- **AND** 拖动期间 `body` 的计算 `cursor` MUST 为 `col-resize`

#### Scenario: 宽度被记住

- **WHEN** 用户把左栏拖到某宽度后刷新页面
- **THEN** 左栏 MUST 以该宽度呈现

#### Scenario: 窄屏不渲染手柄

- **WHEN** 视口宽度小于并置阈值（两栏退化为单栏）
- **THEN** 页面 MUST NOT 渲染分隔手柄

### Requirement: 拖动宽度受上下限约束

左栏宽度 MUST 被夹在上下限之间：下限 MUST 不小于 220px；上限 MUST 同时受「分栏容器宽度减去右栏最小可用宽度（360px）」与 560px 约束，取两者较小值。用户拖到超出范围时 MUST 停在边界，右栏 MUST NOT 被压到 0 宽。

#### Scenario: 拖到最左不会挤没右栏

- **WHEN** 用户把分隔手柄向最左拖动
- **THEN** 左栏宽度 MUST 停在下限（≥220px）
- **AND** 右栏 MUST 仍有可见宽度

#### Scenario: 拖到最右停在边界

- **WHEN** 用户把分隔手柄向右拖到超出容器可容纳的范围
- **THEN** 左栏宽度 MUST 停在「容器宽度 − 360px」与 560px 中的较小值
- **AND** 右栏宽度 MUST 不小于 360px

### Requirement: 分隔手柄可键盘操作且可复位

分隔手柄 MUST 可被键盘聚焦并操作：聚焦后按 ← / → MUST 以 16px 为步长调整（按住 Shift MUST 以 48px 为步长），按 Home / End MUST 直接到下限 / 上限；手柄 MUST 带 `role="separator"`、`aria-orientation="vertical"` 与 `aria-valuenow` / `aria-valuemin` / `aria-valuemax`。双击手柄 MUST 把宽度复位到默认档位（T0 `--layout-pane-left`）。

#### Scenario: 方向键调整宽度

- **WHEN** 键盘聚焦手柄后按两次 →
- **THEN** 左栏宽度 MUST 增加 32px
- **AND** 手柄的 `aria-valuenow` MUST 同步更新

#### Scenario: 双击复位

- **WHEN** 用户把宽度改成非默认值后双击手柄
- **THEN** 左栏宽度 MUST 回到默认档位（280px）
