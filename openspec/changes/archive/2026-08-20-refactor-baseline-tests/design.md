## Context

六步重构序列将移动 `apps/` 下多处代码：枚举与状态机（`models/constants.py`、`models/test_models.py`、`apps/test_runner/state_machine.py`）、算法（`apps/device_inspector/service.py:4/200/372`、`ocr.py`、`apps/device_pool/pool.py:144`）、引擎连接（`pool.py`、`executors/ui/{connect,recovery,adapter}.py`）。移动前行为必须可回归。现状测试覆盖：`tests/device_inspector/` 仅 `test_capture_service.py`；device_pool、test_runner 无专项单测。

## Goals / Non-Goals

**Goals:**

- 为"将被移动的代码"补现状行为基线测试，锚定当前（含已知缺陷）行为
- 全量 pytest 跑通并留存基线结果

**Non-Goals:**

- 不修复任何现状行为（含已知漂移、幽灵状态、"COMPLETED" 大写等）
- 不写目标态契约测试（`Node`/`OcrText` dataclass、`UiEngine` 契约测试归后续 change：extract-algorithms-package、add-engine-protocol）
- 不改任何产品代码、不触数据库

## Decisions

- **测试分层**：纯函数（xpath/ocr/XML 修复）直接单测；设备/引擎相关全 mock（不真连 u2/Airtest/ADB）；cnocr 重依赖打桩 `_get_engine`，不加载真实模型
- **目录**：沿用 tests/ 按 App 组织；`tests/test_runner/` 不存在则新建
- **已知缺陷锚定**：漂移数据（queued+终态）、"COMPLETED" 大写等现状行为用注释标注 `现状行为，L1b change 后此断言将更新`，让后续 change 显式承担断言更新
- **基线留档**：全量 pytest 结果（通过数/失败项）附到本变更完成说明，并勾选 Checklist §一

## 模块防火墙自检

- 纯测试变更：不新增任何产品代码跨 App import；测试 import `apps` 内部属测试豁免（项目惯例）
- 无跨 App 写、无 ORM 写路径变化、无 API 签名变化、前端零改动
- 通过

## Risks / Trade-offs

- [cnocr/torch 重依赖拖慢测试环境] → mock `_get_engine`，不加载真实模型
- [测试锚定已知缺陷，后续 change 改行为需同步改断言] → 每个受影响测试标注"现状行为"注释；对应 change 的 tasks 显式列出"更新该断言"任务
- [基线运行耗时] → 核心用 `pytest -m "unit"` 跑，全量一次留档
