## Context

L1c 详档 §五 定义了 AirtestU2Engine 组合双栈映射与吸收清单（45s/20s 超时、recovery 重连、_addr、BGR→PNG bytes）；§八 列出 6 接触点逐代码块迁移。本变更收敛其中 4 处（connect/recovery/views/service），pool.py 的 3 处（pool/views 裸 adb/collect 之外的部分）随 Step 4 一并收敛——**门禁调整**：Checklist P1 引擎实现行"grep 接触点仅 engines/ 一处"在本变更落地为"仅 engines/ + pool.py（Step 4 收敛，已登记）"。

## Goals / Non-Goals

**Goals:**

- `AirtestU2Engine` 完整实现协议，且通过全 mock 契约测试
- 执行链路 4 处不再直接 import u2/Airtest
- 行为等价：既有执行链路（runner/executor/adapter）与设备管理链路零行为变化

**Non-Goals:**

- 不改 pool.py（DevicePool 单例，Step 4 替代）
- 不激活 `get_device_engine()` 生产消费（DeviceSession 在 Step 4 接入）
- 不处理 executor.py 233/344 的 adapter 旁路（Step 4）
- 不做 Node→dict 反向兼容层（引擎 dump 返回 Node；pool 仍走原 dict 路径，互不影响）

## Decisions

- **DeviceConnection 兼容壳**：connect.py 保持 `check_and_connect(serial)` 签名与 `DeviceConnection` dataclass，内部改由引擎构造——runner/adapter/executor 零改动
- **错误语义**：引擎抛 `EngineConnectError`（技术语义）；connect.py 转 `DeviceCheckError`（执行语义）；views.py 映射 502/504（ATX/离线关键词不变）
- **U2_OP_TIMEOUT 归属**：引擎层（u2 HTTP 调优是引擎实现细节）；`DEVICE_CHECK_TIMEOUT=45` 留 connect.py（执行编排超时）
- **wait_toast 移植**：adapter.wait_for_toast 逻辑移植到引擎（无 stopped 回调，仅时间截止）；executor 仍走 adapter（Step 4 切换）
- **契约测试口径**：tests/engines/test_airtest_u2_contract.py 全 mock（不真连设备），覆盖连接关键词判定/超时/ATX 消息、screenshot bytes 格式、dump 3 层 fallback→Node、exists/get_text/wait_toast 冒烟、reconnect

## 模块防火墙自检

- `engines/android/airtest_u2.py` 只 import：uiautomator2/Airtest/PIL（第三方）、`algorithms.hierarchy`（纯函数，D-2 允许 models，algorithms 是纯函数包，L1c 详档 §三 已有先例说明？——**此处修正**：防火墙规定 engines ❌ algorithms.*；hierarchy 解析是纯函数、零 apps 依赖，属算法层能力复用。登记为「⚠️ 契约出入」：engines import `algorithms.hierarchy`（纯解析，无状态），评审确认；若否决，解析逻辑内联进引擎）
- 业务 App（device_pool/test_runner）import engines 属跨层调用引擎实现——本变更阶段允许（DeviceSession 未落地前的过渡）；Step 4 后经协议层收敛
- 无 ORM 写变化；前端零改动
- 通过（附 2 处登记）

## Risks / Trade-offs

- [engines import algorithms 违反总纲 §三 字面禁令] → 纯解析复用优于内联；登记契约出入，Step 4 评审时一并裁决
- [执行链路过渡期直接 import 引擎实现] → Step 4 DeviceSession 落地后收敛为协议消费，本变更在 tasks 显式标注过渡性
- [重连/连接行为差异] → 关键词、超时、异常文案逐字移植；基线测试重写为引擎契约测试并对照原断言
- [pool.py 未收敛导致 grep 门禁不纯] → 门禁调整为"engines/ + pool.py"，Checklist 同步登记
