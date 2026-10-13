## MODIFIED Requirements

### Requirement: 引擎零 apps 依赖

`ai_engines` SHALL 不 import `apps.*` 内部实现；数据类业务工具经 `TaskRequest.tools` 注入，引擎只负责包装与调用；设备动作类工具 SHALL 由引擎自带（设备工具 + 登记清单），不再经注入，装配时 MUST 跳过注入清单里的同名设备动作工具。`ai_engines` 是唯一可触碰第三方 AI 框架的层。引擎 MUST NOT 直接引用具体设备实现（只能经设备引擎协议），也 MUST NOT 因设备动作而获得对设备池台账与设备日志的直接访问。

#### Scenario: 工具注入

- **WHEN** 引擎需要平台数据类工具（如页面流文档）
- **THEN** 工具函数由 Django 层注入（`TaskRequest.tools`），引擎不直接 import `apps` 业务模块

#### Scenario: 设备动作不经注入

- **WHEN** 引擎装配设备动作工具
- **THEN** 它使用引擎自带的设备工具，注入清单里的同名设备动作工具被跳过，模型可见的设备动作只有一份

#### Scenario: 引擎不碰设备实现与台账

- **WHEN** 引擎执行设备动作
- **THEN** 它只经设备引擎协议（协议实现或替身）取设备句柄，不 import 具体设备实现、不读写设备池台账、不直接访问设备日志
