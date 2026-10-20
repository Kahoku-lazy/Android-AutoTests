## Context

见 `proposal.md` 的 Why。设计上需要承接的现状事实：

- `System._CONTROL["android"]` 只登记 `AndroidControl` 一个实现类（`engines/device/android/android_device.py:709`），`open_device` 返回的控制对象一律是它；三个截图调用点（`engines/agents/tools/tool_device.py:75`、`tool_ocr.py:101`、`apps/device_inspector/service.py:72`）都经它。
- `AndroidControl.__init__` 目前无条件 `u2.connect(serial)`，而截图走的是 `AdbControl.screenshot_bytes` → `adb exec-out screencap -p`，一个 u2 调用都不需要（`android_device.py:644-656`）。
- 截图工具契约是「只回 `image.base64` / `image.media_type`、不落盘、参数只有 `serial`」（`openspec/specs/ai-device-action/spec.md:94-96`），实现与测试已按此落地；模型永远拿不到路径。
- `executor_prompt.py:13-14` 要求模型「用 OCR 工具重新识别定位」，但 `ocr_page` 只存在于 `tool_ocr.py` 且不在 `select_tools` 的候选表里（`tools_config.py:54`），现行 `ai-screen-vision` 规格明确要求它 MUST NOT 装配给角色。

## Goals / Non-Goals

**Goals**

- 截图链路上「模型能拿到什么」在规格、提示词、代码三处完全一致：只有图片，没有路径。
- 截图与 uiautomator2 生命周期解耦，且不需要改任何调用点的签名。
- 提示词不再引导模型调用不存在的工具。

**Non-Goals**

- 不恢复截图落盘与「点击后截图路径」取证（用户已决策：以现行代码为准）。
- 不动 `click_timer` / `logAssertionTimer` / `logAssertionInfo` 等已无实现承载的条目，也不重建「日志检查块」装配链路。
- 不改前端组件与 DTO（前端已有空值分支与存量旧值分支）。
- 不新增 `open_device` 参数、不新增控制实现类。

## Decisions

### D1：u2 会话在 `AndroidControl` 内部惰性建立

做法：`AndroidControl.__init__` 只做 `super().__init__(serial)`（`AdbControl` 已备好 `log` / `adb` / `info`），把 `device` 改为**首次访问才连接**的惰性属性并缓存实例；`find_xpath` 与 `input_text` 走该属性，其余方法（点击、长按、滑动、拖动、按键、启停、截图、dump）完全不碰 u2。

理由：
- 一处改动即覆盖全部三个截图调用点，不需要在每个调用点区分「要不要 u2」；`device_inspector` 与 OCR 链路自动受益。
- 不新增 API 面，`System` 登记表、`open_device` 签名、上层调用保持原样，符合「上层只经 action 拿能力」的既有分层。
- 对比「新增纯 adb 控制入口（如 `open_device(..., ui=False)`）」：需要在 3 个调用点做选择、还要给 `System` 加第二个控制登记，读代码的人得先判断「这次要不要 u2」，成本高于收益。
- 对比「截图工具单独用 `AdbControl`」：只解决智能体这一条链，检查器与 OCR 仍付 u2 连接；且 `_device` 上下文是通用动作入口，截图为它单开一套会带来两个控制对象的生命周期问题。

惰性属性被多个方法连续访问时复用同一实例，不重复连接；连接失败时抛 `RuntimeError` 并带「uiautomator2 连接失败」前缀，与 adb 通道错误可区分。

### D2：提示词删除 OCR 表述，不装配 OCR 工具

做法：`executor_prompt.py` 第 4、5 条改为「视觉归一化坐标 → xpath」两级重试，删掉「OCR 工具」字样；`tool_ocr.py` 与 `ai-screen-vision` 的「不装配给角色」要求保持不变。

理由：现行规格已经站在「不装配」一侧（`ai-screen-vision` 的「OCR 工具实现保留在引擎工具层且不装配给角色」），提示词是唯一偏离方，改提示词是让三者一致的最小动作。反向装配 `ocr_page` 会让每次定位多一条重依赖链路（cnocr）与一个模型可见工具，属于扩需求。

### D3：`screenshot` 字段保留键、口径改为恒空；存量旧值照旧呈现

做法：规格里把 `screenshot` 的取值来源改为「不采集、恒为空字符串」，把任务详情页/日志检查块里的「截图路径」改为「是否截图的取证标记」；**不删字段、不改前端**。

理由：
- 删字段是对外契约的 BREAKING 变更，要同步 DTO、类型、存量记录与三个消费方；而「键在、值为空」与现行前端分支（「未截图如实标注」）天然兼容，风险最低。
- 存量记录里可能已经有路径（历史落盘时代写入），规格显式保留「存量旧值按文本呈现、可看原图」，避免把历史数据变成不可读。
- 为什么不是「恢复落盘」：截图工具的核心用途是把图喂给视觉模型；落盘会重新引入「同一帧编两次/写两次」与磁盘清理生命周期，且用户已决策以代码为准。

### D4：解耦后不在截图工具里补任何「等待 u2 就绪」逻辑

做法：截图成功即成功，u2 是否可用与截图结果无关；不重试、不预热、不探测。

理由：加探测会把 u2 依赖以更隐蔽的方式带回来，也让截图耗时随 u2 状态波动；截图只需要 adb。

## Risks / Trade-offs

- [u2 连接错误从「打开设备时」推迟到「用 xpath / 输中文时」] → 错误仍在同一工具调用内抛出并被 `_execute` / 工具层转成可读 `error`；错误文案带「uiautomator2」前缀，排查时能直接看出是 u2 侧问题。
- [惰性属性在多线程/多协程下被并发初始化] → 工具层只读工具可并发、写工具串行；截图只读且不访问该属性，xpath 属只读但会访问，因此属性初始化用「一次赋值 + 已存在即复用」的朴素写法即可，不做双检锁，避免引入不必要的复杂度。
- [新记录 `screenshot` 恒空，历史记录有值，同一页面出现两种形态] → 规格按「新记录不呈现路径 / 存量旧值仍呈现」分别写死，前端两分支都已存在。
- [不落盘后无法事后取证「这一步当时屏幕是什么」] → 取证能力由过程日志（工具返回记 `media_type` 与 base64 长度）与验收模型的截图输入承担；如需人工回看历史帧，需另起变更（记为债务，不在本单）。

## Migration Plan

- 无数据迁移：提示词是代码常量，规格是文档；不动 Django 迁移。
- 发布顺序无要求：代码改动只影响运行时行为（u2 惰性 + 提示词文案），归档后主规格自动承接 delta。
- 回滚：还原 `android_device.py` 的 `AndroidControl` 与 `executor_prompt.py` 即可；规格回滚按归档前的 delta 反向撤销。

## Open Questions

无。三处取舍已在 2026-10-20 会话中确认：提示词改（不装配 OCR）、规格以代码为准（screenshot 不采集）、u2 解耦。
