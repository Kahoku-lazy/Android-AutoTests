"""engines — 可替换引擎层（设备引擎 + SOP + 页面文本识别）。

- engines.device：设备引擎。对外入口是 action。
- engines.agents：控制设备任务的 SOP。平台启动时传入执行与验收模型。
- engines.vision：页面文本识别。只供引擎 OCR 工具调用。

导入边界：零 apps.*、零 django.*（业务工具经注入）。
"""
