"""engines — 可替换引擎层（设备引擎 + AI 引擎统一入口）。

- engines.device：设备引擎（L1c），UiEngine 协议 + registry + u2 实现。
- engines.ai：AI 引擎（L1c），AiEngine 协议 + registry + AgentScope 实现。

导入边界：零 apps.*、零 django.*（业务工具经注入）。
"""