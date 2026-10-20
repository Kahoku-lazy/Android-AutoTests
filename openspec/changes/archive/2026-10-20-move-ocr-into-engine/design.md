## Context

见 proposal.md - Why。现状：`utils/vision/ocr.py` 提供 `recognize`；`apps/device_inspector/service.py` 的 `capture_ocr_payload` 与 `ocr_page_payload` 调用它；`api.capture_snapshot` 在 `method=ocr` 时走前者，`api.ocr_screen` 走后者。`ocr_screen` 在白名单中，仓库内已无业务调用方。引擎工具 `engines/agents/tools/tool_ocr.py` 在函数内部惰性导入同一识别模块。前端抓取固定发 `dump`。

层级解析仍在 `utils/xpath.py`、`utils/hierarchy.py`、`utils/element_layers.py`。本设计不移动这三份。

## Goals / Non-Goals

**Goals:**

- 识别包落在 `engines/vision/`，且全仓库只有 `engines/agents/tools/tool_ocr.py` 导入它。
- 检查器抓取只接受 `dump`；删除检查器侧的识别函数与白名单入口。
- 不改表结构。新抓取的 `ocr_json` 为空、`ocr_count` 为 0。历史行原样可读。

**Non-Goals:**

- 不把识别装配进执行或验收角色的工具集。
- 不改元素定位的页面级 `ocr_json`，不清空历史快照。
- 不改检查器页面交互，不改快照详情里读出历史 `texts` 的响应形状。
- 不改 `engines/device` 的取数职责，不让设备引擎导入识别包。

## Decisions

### D1 包落点为 `engines/vision/`

与 `engines/device`、`engines/agents`、`engines/uart_log` 平级。识别不是设备动作，放进 `engines/device/vision/` 会把算法和截图、点击绑在同一包里。

旧路径不留转发模块。活代码只有两处导入，一处删除、一处改到新路径。

### D2 调用面收成引擎工具一处

`tool_ocr._recognize` 改为惰性导入 `engines.vision.ocr.recognize`。`cnocr` 仍由识别模块在被导入时加载，工具模块顶层不导入识别包，避免引擎启动拉起重依赖。

`engines/device` 与 `apps/` 均不得导入 `engines.vision`。用源码扫描测试锁住：命中 `engines.vision` 的 Python 文件只有 `engines/vision/` 自身、`engines/__init__.py` 的包说明，以及 `engines/agents/tools/tool_ocr.py`。

### D3 检查器删执行、留历史列

删除 `service.capture_ocr_payload`、`service.ocr_page_payload` 与 `api.ocr_screen`（含 `__all__`）。`capture_snapshot` 只接受 `dump`；其他 `method` 沿用现有 `CaptureError`（400，「无效的获取方法」），不落库。成功路径始终写入空 OCR 载荷。

`Snapshot.method` / `ocr_json` / `ocr_count` 列保留。`snapshot_to_dict` 与 `snapshot_meta_dict` 继续读出已存字段，历史详情形状不变。注释改为：新抓取只有 `dump`，历史行的 `method` 仍可能是 `ocr`。

备选：删列并迁移。否决。存量详情还在读这些字段，删列会改响应契约，超出「停止执行识别」的范围。

### D4 前端只改过时说明

`frontend/src/modules/device-inspector/store.ts` 里「后端 method 入参保留但前端不再发 ocr」改为抓取只接受 `dump`。快照列表对历史 `method=ocr` 的文字标签保留，界面本来就不展示 OCR 计数与框选。

## 模块防火墙自检

- 不新增跨 App import。检查器去掉对 `utils.vision` 的导入；引擎工具只导入 `engines.vision`，不导入 `apps`。
- 不新增跨 App 的 service / runner / consumer / state_machine 导入。
- 快照写入仍在 `apps/device_inspector/api.py`。本变更减少写入分支，不新增写路径。
- 前端不直连数据库。仪表盘无写操作。
- 删除 `ocr_screen` 去掉一个已无调用方的进程内入口，不新增跨模块依赖。

## Risks / Trade-offs

- [仓库外脚本仍调用 `ocr_screen` 或 `method=ocr`] → 仓库内无业务调用方；`method=ocr` 返回 400 且不落库。进程内入口直接删除，不留兼容包装。
- [历史详情仍带回 `texts`] → 规格写明只读历史、界面不展示。新抓取的 `texts` 为空、`ocr_count` 为 0。
- [有人在引擎启动路径导入 `engines.vision`] → 源码扫描限定唯一调用文件，且该文件保持函数内导入。

## Migration Plan

无数据库迁移。回滚即恢复删除前的包位置与检查器识别函数。历史行不改，回滚后仍可读取。

## Open Questions

无。
