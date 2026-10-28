## ADDED Requirements

### Requirement: 麦克风输入可观测且无输入可提示

会话进行中，页面 SHALL 显示麦克风状态，至少区分「未采集到音频」「有信号、等待说话」「有输入」三种状态，并显示随音量变化的电平。服务端 SHALL 统计每个会话的上行音频帧数与字节数，并写入该会话的 `session_end` 记录。实时语音会话就绪后 6 秒内未收到任何上行音频帧时，服务端 SHALL 下发一条非致命提示，页面 MUST 以可读文案提示用户检查系统默认输入设备与浏览器麦克风权限，且 MUST NOT 因此关闭会话。

#### Scenario: 有声音时电平更新

- **WHEN** 用户对着麦克风说话且浏览器已授权
- **THEN** 页面麦克风状态显示「有输入」，电平条随音量变化

#### Scenario: 设备静音时可见

- **WHEN** 麦克风已授权但持续没有音频帧
- **THEN** 页面麦克风状态显示「未采集到音频」
- **AND** 服务端在 6 秒后下发一次检查输入设备与权限的提示

#### Scenario: 会话结束记录音频帧数

- **WHEN** 一次语音会话结束
- **THEN** `logs/knowledge_assistant/YYYY-MM-DD.jsonl` 的 `session_end` 记录包含 `audio_frames` 与 `audio_bytes`
- **AND** 有正常说话时 `audio_frames` 大于 0

#### Scenario: 无输入提示不关闭会话

- **WHEN** 服务端下发无输入提示
- **THEN** 页面显示提示但仍保持「聆听中」，用户可切换设备后继续
