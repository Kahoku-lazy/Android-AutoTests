## Context

见 `proposal.md`。实测证据（2026-10-20，H6810 / 端口 7005）：

- `diy_configs_set_success` 全量日志命中 **0 次**；`scene_configs_set_success` 4 次、`music_configs_set_success` 8 次（这两个能被验收正确命中）。
- 四次 DIY 点击后设备都打印 `diy2d_mode stop` + `diy2d_mode_start`，时间点与点击逐一吻合（如点击 16:14:46,324 → 16:14:47,015 start）。
- 关键词表结构为 `{keyword: [{id, module, feature}]}`，同一条目当前挂 `id=23 / DIY模式 / DIY灯效设置成功`。

## Goals / Non-Goals

**Goals**：让 DIY 断言的日志证据在 H6810 上可命中，避免「UI 成功但判 FAIL」。

**Non-Goals**：不改 `check_device_log` 的窗口与判定口径；不改验收模型提示词；不处理「一个功能点对应多个同义关键词」的通用建模（当前表一张词一个功能点）。

## Decisions

### D1 替换而非并列

做法：删 `diy_configs_set_success`，把 `id=23` 挂到 `diy2d_mode_start`。

理由：验收模型是「从表里选一个关键词原文去检查」。同一功能点并列两个词时，模型选哪个不确定，选到固件不打的词仍会误判——这正是本次要消除的失败模式。若将来有其它机型确实打 `diy_configs_set_success`，再按机型补词并同步调整提示词口径，不在本单提前铺开。

### D2 只改配置、不动代码

`check_device_log` 按关键词原文匹配，关键词来自配置文件；改表即生效于下一次验收，无需改工具。

### D3 生效时机

关键词表在平台启动时加载一次，改完必须重启平台才用于判定——与页面「如实说明生效时机」的既有口径一致。

## Risks / Trade-offs

- [其它固件版本可能打旧词] → 本单只服务当前 H6810 现场；若出现其它版本，单独立项按机型补词（届时需要「一个功能点可挂多词」的表结构变更）。
- [`diy2d_mode_start` 同时出现在 `diy_mode_start` 语义附近（切换 DIY 模式也会打）] → 风险可控：DIY 用例的断言是「设置灯效成功」，而设置灯效必然伴随 stop/start；若误判为通过，属于放宽而非收紧，需在验证时对两次点击各查一次以确认。
- [改表后忘记重启] → 任务里明确要求重启并复核。

## Migration Plan

1. 编辑 `config/device_log_keywords.json`。
2. 重启平台（`python run.py stop && python run.py start`）。
3. 重跑 DIY 用例第 4 步验证命中；回滚即还原该条并重启。

## Open Questions

无。
