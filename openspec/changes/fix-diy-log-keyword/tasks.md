## 1. 改关键词表

- [ ] 1.1 `config/device_log_keywords.json`：删除 `diy_configs_set_success` 条目，把 `diy2d_mode_start` 的条目补为 `{"id": 23, "module": "DIY模式", "feature": "DIY灯效设置成功"}`（保持 `id` 不变，避免下游按 id 关联失效）。验证：`python -c "import json;d=json.load(open('config/device_log_keywords.json',encoding='utf-8'));print('diy2d_mode_start' in d, 'diy_configs_set_success' in d, d.get('diy2d_mode_start'))"` 输出 `True False [{'id': 23, ...}]`
- [ ] 1.2 确认 JSON 合法且仍能被子串匹配加载。验证：`python -m pytest tests -q -k "keyword or log_read"`（相关用例通过；无匹配用例时记录 0 项）

## 2. 重启与验证

- [ ] 2.1 重启平台使新表生效：`python run.py stop; python run.py start`。验证：`python run.py status` 后端 ONLINE；串口日志页「日志关键词」Tab 里 DIY 灯效设置成功显示为 `diy2d_mode_start`
- [ ] 2.2 重跑 DIY 用例第 4 步（`temps/cases/h6810_scene_music_diy.yaml` 的 DIY 步骤，真机 R5CT62RH88F）：两次点击后各查一次 `diy2d_mode_start`，期望两次均 PASS。验证：`logs/agents/agent_events.log` 里第 4 步判决为 `passed=True`，并给出两次命中时间戳
- [ ] 2.3 回归场景 / 音乐两步（同一用例的第 2、3 步）确认关键词改动未影响它们。验证：事件日志中第 2、3 步仍 `passed=True`
