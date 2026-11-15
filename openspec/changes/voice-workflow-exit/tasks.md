## 1. 出口

- [x] 1.1 新增 `engines/agents/workflow/voice/`，对外导出打开会话、就绪状态和浏览器音频传输。内部可调用现有 `realtime_vocie`，但出口内不得直接构造 `RealtimeAgent`。验证：`python -c "from engines.agents.workflow.voice import open_voice_session, build_runtime_status, WebSocketAudioTransport"` 成功。
- [x] 1.2 打开会话时只经 `assistant.create_voice_agent` 取得语音智能体；传输由调用方传入，workflow 不关闭浏览器通道。验证：新增单测用假传输断言创建出口被调用，且源码扫描无 `RealtimeAgent(`。
- [x] 1.3 从 workflow 出口再导出文字会话仍需要的转写桥与日志协议。验证：`knowledge_chat` 改为从该出口导入后，`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_chat_session.py -q` 通过。

## 2. 后端改道

- [x] 2.1 `backend/apps/knowledge_assistant` 的 consumer、runtime、views 改为只 import `workflow.voice`。验证：`rg "realtime_vocie" backend` 无匹配；`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_assistant_consumer.py tests/knowledge/unit/test_knowledge_assistant_config.py -q` 通过。
- [x] 2.2 知识库传输与事件桥测试改经 workflow 出口导入。验证：`python -m pytest -c tests/pytest.ini tests/knowledge/unit/test_knowledge_assistant_transport.py tests/knowledge/unit/test_knowledge_assistant_events.py -q` 通过。

## 3. 边界

- [x] 3.1 更新 `workflow/voice` 与 `realtime_vocie` 的 AGENTS：前者是对外出口，后者是内部实现。验证：两份文档的依赖方向与代码 import 一致。
- [x] 3.2 注释与边界自检。验证：`python -m scripts.docstrings check` 对本次 engines 改动无新 error；`python utils/gen_arch_stats.py --check-boundaries` 通过。
