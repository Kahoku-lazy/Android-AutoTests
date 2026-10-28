# knowledge_assistant 模块 AGENTS.md

> **AGENTS 层级**：二级约束 —— 根 `AGENTS.md` 与上级 `backend/apps/AGENTS.md` 优先于本文件（本文件只写增量）。

## 入口与职责

- HTTP：`GET /api/knowledge-assistant/status/`（登录可读）只返回就绪状态，不返回密钥。
- WS：`/ws/knowledge-assistant/?token=<access_token>&mode=<omni|pipeline>` 是平台**唯一**实时语音通道；只承载本会话的音频、转写、打断与播放进度。
- 该 consumer **不接 channel layer**（单连接、无 group 广播）：音频帧高频，走 Redis 会把一次抖动放大成 1011 断线；`__call__` 只保留 `receive → dispatch` 直连路径。
- 前端入口：`/knowledge-assistant`，侧栏「AI 功能」分组的第二项。
- **AgentScope 相关实现**（实时模型配置/工厂、提示词、事件桥、`RealtimeAgent` 会话、`PipelineVoiceSession`、`TransportBase` 传输）一律放 `engines/agents/realtime_vocie/`；本 App 不重复实现。
- 路线由握手 query `mode` 决定：`omni` 走 `RealtimeVoiceSession`，`pipeline` 走 `PipelineVoiceSession`；Pipeline 额外支持 `text` 消息做纯文本提问。

## 模块划分（接入层）

| 文件 | 职责 |
| --- | --- |
| `consumer.py` | WS 生命周期、JWT 校验、白名单控制消息、调用引擎会话 |
| `runtime.py` | 对话日志目录解析 + 状态 payload（引擎状态 + `log_dir/log_file`） |
| `transcript_log.py` | 按自然日追加 `logs/knowledge_assistant/YYYY-MM-DD.jsonl` |
| `views.py` / `urls.py` | 就绪状态 HTTP 接口 |
| `apps.py` | Django App 配置 |

引擎侧见 `engines/agents/realtime_vocie/AGENTS.md`。

## 红线

1. **RAG 边界**：允许 `engines/agents/rag` 读取 `D:\Govee\data\rag_data` 的只读本地资料并注入 Pipeline LLM；不得引入文档上传 UI、平台知识库写接口、外部向量库服务或前端 RAG 管理入口。
2. **密钥不出服务端**：`DASHSCOPE_API_KEY` 不得出现在 HTTP/WS 响应、日志或前端代码。
3. **日志边界**：对话档案只写 `logs/knowledge_assistant/`，不写 `project-log` 的四组运行日志；运行期异常写 `backend_log`。
4. **不写库**：本 App 无 Model、无 migration；对话记录是文件档案，不进入 ORM。
5. **WS 白名单**：客户端只能发 `interrupt`、`played` 与 Pipeline 的 `text`；不得把任务、设备、文件或平台写操作接进本通道。
6. **会话释放**：断连、离开页面、异常都必须关闭模型会话、音频传输并写 `session_end`。
7. **不反向依赖**：本 App 可以 import `engines.agents.realtime_vocie`；引擎不得 import `backend.apps.*`。

## 快速验证

```powershell
python manage.py check
ruff check backend/apps/knowledge_assistant engines/agents/realtime_vocie
python -m pytest -c tests/pytest.ini tests/graybox/unit/test_knowledge_assistant_*.py
```
