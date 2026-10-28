"""task-list serializers — task submission input."""

from rest_framework import serializers


class TaskSubmitInputSerializer(serializers.Serializer):
    """任务提交入参 — title/agent_id 必填；设备由任务类型在视图层校验。

    device_control 任务必须有 device_serial；case_authoring 任务必须上传
    documents（PRD/Word），不需要设备与 YAML。
    """

    title = serializers.CharField(required=True, allow_blank=False)
    agent_id = serializers.IntegerField(
        required=True,
        min_value=1,
        error_messages={
            "required": "请选择智能体",
            "invalid": "智能体 id 必须为数字",
            "min_value": "请选择智能体",
        },
    )
    device_serial = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        error_messages={"invalid": "请选择设备"},
    )
    case_title = serializers.CharField(required=False, allow_blank=True, default="")
    goal = serializers.CharField(required=False, allow_blank=True, default="")
    assistant_route = serializers.CharField(required=False, allow_blank=True, default="")
    device_label = serializers.CharField(required=False, allow_blank=True, default="")
    attachment = serializers.FileField(required=False, allow_null=True)

    def validate_title(self, value):
        title = (value or "").strip()
        if not title:
            raise serializers.ValidationError("任务标题不能为空")
        return title

    def validate_goal(self, value):
        return (value or "").strip()

    def validate_assistant_route(self, value):
        route = (value or "").strip()
        if route and route != "device_control":
            raise serializers.ValidationError("请选择平台小助手上的助手")
        return route

    def validate_device_serial(self, value):
        return (value or "").strip()

    def validate_case_title(self, value):
        return (value or "").strip()

    def validate_device_label(self, value):
        return (value or "").strip()

    def validate_attachment(self, uploaded):
        if uploaded is None:
            return None
        name = getattr(uploaded, "name", "") or ""
        ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
        if ext not in {".docx", ".pdf"}:
            raise serializers.ValidationError("仅支持 Word（.docx）与 PDF")
        size = getattr(uploaded, "size", None)
        if size is not None and size > 20 * 1024 * 1024:
            raise serializers.ValidationError("文件过大")
        return uploaded
