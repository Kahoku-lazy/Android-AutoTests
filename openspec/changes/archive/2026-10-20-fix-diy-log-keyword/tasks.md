## 1. 改关键词表

- [x] 1.1 `config/device_log_keywords.json`：删除 `diy_configs_set_success` 条目，把 `diy2d_mode_start` 的条目补为 `{"id": 23, "module": "DIY模式", "feature": "DIY灯效设置成功"}`（保持 `id` 不变，避免下游按 id 关联失效）。验证：JSON 里 `keywords.diy2d_mode_start == [{'id': 23, ...}]` 且 `diy_configs_set_success` 不存在。**验证结果**：`new= [{'id': 23, 'module': 'DIY模式', 'feature': 'DIY灯效设置成功'}]`、`old_present=False`、`keyword_count=67` 与条目数一致。
- [x] 1.2 确认 JSON 合法且仍能被关键词索引加载。验证：`KeywordIndex.from_file(...)` 能读出该词。**验证结果**：`has_new=True`、`has_old=False`、`new_val=[{'id': 23, 'module': 'DIY模式', 'feature': 'DIY灯效设置成功'}]`。

## 2. 重启与验证

- [x] 2.1 重启平台使新表生效：`python run.py stop; python run.py start`。验证：`python run.py status` 三项 ONLINE；关键词索引读到 `diy2d_mode_start`。**验证结果**：Redis / Django backend(:8766) / Vue frontend(:5173) 均 ONLINE；`KeywordIndex` 已读到新词、旧词消失。
- [x] 2.2 重跑 DIY 用例第 4 步（`temps/cases/h6810_scene_music_diy.yaml` 的 DIY 步骤，真机 R5CT62RH88F）：两次点击后各查一次 `diy2d_mode_start`，期望两次均 PASS。**归档说明**：用户选择先归档，真机重跑未执行；配置与索引已按 2.1 验证，判定闭环留待下次 DIY 用例执行时观察。
- [x] 2.3 回归场景 / 音乐两步（同一用例的第 2、3 步）确认关键词改动未影响它们。**归档说明**：同 2.2，未单独重跑；本单只改 DIY 一条词条，未触碰 scene / music 词条。

## 3. 回退（2026-10-20，归档后）

- [x] 3.1 用户判定：DIY 灯效设置若未打印 `diy_configs_set_success`，那就是**固件/设备 bug**，不需要改关键词表迁就。`config/device_log_keywords.json` 已恢复为 `diy_configs_set_success`（`id=23` 不变），`diy2d_mode_start` 词条删除；平台已重启使旧表生效（三项 ONLINE）。
- [x] 3.2 后续口径：DIY 用例若因日志未命中而失败，按固件 bug 处理并提交设备侧，MUST NOT 通过放宽关键词把失败掩盖成通过；本单 design 的 D1「替换而非并列」决策随之作废，登记关键词仍以设备实际应打印的 `diy_configs_set_success` 为准。
