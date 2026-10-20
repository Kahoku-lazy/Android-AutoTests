## 1. 改关键词表

- [x] 1.1 `config/device_log_keywords.json`：删除 `diy_configs_set_success` 条目，把 `diy2d_mode_start` 的条目补为 `{"id": 23, "module": "DIY模式", "feature": "DIY灯效设置成功"}`（保持 `id` 不变，避免下游按 id 关联失效）。验证：JSON 里 `keywords.diy2d_mode_start == [{'id': 23, ...}]` 且 `diy_configs_set_success` 不存在。**验证结果**：`new= [{'id': 23, 'module': 'DIY模式', 'feature': 'DIY灯效设置成功'}]`、`old_present=False`、`keyword_count=67` 与条目数一致。
- [x] 1.2 确认 JSON 合法且仍能被关键词索引加载。验证：`KeywordIndex.from_file(...)` 能读出该词。**验证结果**：`has_new=True`、`has_old=False`、`new_val=[{'id': 23, 'module': 'DIY模式', 'feature': 'DIY灯效设置成功'}]`。

## 2. 重启与验证

- [x] 2.1 重启平台使新表生效：`python run.py stop; python run.py start`。验证：`python run.py status` 三项 ONLINE；关键词索引读到 `diy2d_mode_start`。**验证结果**：Redis / Django backend(:8766) / Vue frontend(:5173) 均 ONLINE；`KeywordIndex` 已读到新词、旧词消失。
- [ ] 2.2 重跑 DIY 用例第 4 步（`temps/cases/h6810_scene_music_diy.yaml` 的 DIY 步骤，真机 R5CT62RH88F）：两次点击后各查一次 `diy2d_mode_start`，期望两次均 PASS。验证：`logs/agents/agent_events.log` 里第 4 步判决为 `passed=True`，并给出两次命中时间戳
- [ ] 2.3 回归场景 / 音乐两步（同一用例的第 2、3 步）确认关键词改动未影响它们。验证：事件日志中第 2、3 步仍 `passed=True`
