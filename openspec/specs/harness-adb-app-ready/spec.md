# harness-adb-app-ready Specification

## Purpose

约定引擎侧「启动被测 App」工具的就绪判定与首屏同返契约：用哪个信号判断应用「已经可交互」、等待的上限与稳定窗口怎么返回，以及首屏画面能不能随同一次调用交给模型。它决定模型在启动阶段是否需要连拍截图等待，也决定一次启动调用要花多少墙钟与多少 token。

## Requirements

### Requirement: 启动工具在返回前等待应用就绪

`adb_app_start` SHALL 在默认参数下等待应用就绪后再返回，MUST NOT 只把拉起命令打出去就返回。

就绪判定 MUST 同时满足两条：当前前台包名等于目标包名；自本轮最后一次前台变化起，前台 Activity 连续稳定 `settle_ms`（默认 1200 ms）。MUST NOT 只用「前台包名匹配」判定就绪——存在启动页的应用在启动页阶段包名就已经匹配，但 Activity 随后还会切换。

稳定窗口 MUST 以首次采样为起点计时，因此「应用本就在目标前台」与「采样一度取不到前台组件」都不会让等待拖到超时。

等待 MUST 有上限（默认 12 s），超时 MUST 返回 `ready=false` 且 `timed_out=true`，MUST NOT 抛错或阻塞到调用方超时。

返回体 MUST 至少包含：`ready`、`timed_out`、`activity`、`activity_changes`（按出现顺序去重的非空前台组件）、`waited_ms`、`polls`。

#### Scenario: 有启动页的应用等到主界面

- **WHEN** 对一个先显示启动页、再切主界面的应用调用 `adb_app_start`
- **THEN** 返回 `ready=true`
- **AND** `activity_changes` 的最后一项等于 `activity`，且是稳定后的主界面

#### Scenario: 已在目标前台的启动不拖到超时

- **WHEN** 应用已经在目标前台，再次调用 `adb_app_start`
- **THEN** 稳定窗口从首次采样算起，在 1 s 量级返回 `ready=true`
- **AND** 不等到等待上限

#### Scenario: 加载慢的应用不阻塞调用方

- **WHEN** 应用在等待上限内仍未就绪
- **THEN** 返回 `ready=false` 与 `timed_out=true`
- **AND** 调用不抛错，`waited_ms` 约等于上限

#### Scenario: 就绪不靠包名判定

- **WHEN** 前台包名已等于目标包名，但前台 Activity 仍在变化（还在启动页）
- **THEN** 工具继续等待，稳定计时随变化重置，MUST NOT 提前返回 `ready=true`

### Requirement: 首屏画面可随启动结果同返

`adb_app_start` SHALL 支持把就绪后的首屏画面随同一次调用返回（`with_screen=True`）：结果为「JSON 元信息 + 一张图片块」，MUST 与截图工具用同一套截图与压缩实现。

`with_screen` 默认关闭；关闭时返回形状 MUST 与既有纯 JSON 文本一致。

返回的图片 MUST 计入上下文图片数上限，且 MUST NOT 额外落盘。

#### Scenario: 一次调用拿到「已就绪 + 画面」

- **WHEN** 以 `with_screen=True` 调用 `adb_app_start`
- **THEN** 结果里同时有就绪元信息与首屏图片
- **AND** 模型不必再单独调用一次截图工具

#### Scenario: 不开启时形状不变

- **WHEN** 以默认参数调用 `adb_app_start`
- **THEN** 返回仍是纯 JSON 文本
- **AND** 不含图片块

### Requirement: 关闭等待时保持旧行为

`adb_app_start` MUST 接受 `wait_ready=False`：此时 MUST NOT 轮询前台状态，MUST 保持既有「拉起即返回」的行为与字段。

#### Scenario: 关掉等待立即返回

- **WHEN** 以 `wait_ready=False` 调用 `adb_app_start`
- **THEN** 在拉起命令返回后立即返回
- **AND** 返回体不含就绪字段

### Requirement: 执行侧按就绪信号决定是否复截

执行角色的运行提示 MUST 约定：启动类工具返回 `ready=true` 时，模型最多补一张确认截图；`ready=false` 或 `timed_out=true` 时才按需连拍。

该约定 MUST NOT 改变截图工具本身的行为。

#### Scenario: 就绪后不再连拍

- **WHEN** 启动工具返回 `ready=true` 且带首屏图
- **THEN** 模型直接按画面定位，不再连拍截图等待

#### Scenario: 未就绪时仍可连拍

- **WHEN** 启动工具返回 `ready=false`
- **THEN** 模型仍可以连续截图等待加载
