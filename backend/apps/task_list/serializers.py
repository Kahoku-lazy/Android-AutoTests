"""task-list serializers — task submission input."""

import json

from rest_framework import serializers

CASE_SOURCE_YAML = "yaml"
CASE_SOURCE_PLATFORM = "platform"


class TaskSubmitInputSerializer(serializers.Serializer):
    """任务提交入参 — title/agent_id 必填；设备由任务类型在视图层校验。

    device_control 任务必须有 device_serial，用例来源二选一：``yaml`` 上传配置
    文件，或 ``platform`` 给用例编号列表（JSON 数组字符串）。case_authoring 任务
    必须上传 documents（PRD/Word），不需要设备与 YAML。
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
    case_source = serializers.ChoiceField(
        required=False,
        choices=[CASE_SOURCE_YAML, CASE_SOURCE_PLATFORM],
        default=CASE_SOURCE_YAML,
    )
    case_ids = serializers.CharField(required=False, allow_blank=True, default="")
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

    def validate_case_ids(self, value):
        """把 JSON 数组字符串收成用例编号列表。

        Raises:
            serializers.ValidationError: 不是 JSON 数组，或元素不是非空字符串。
        """
        text = (value or "").strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise serializers.ValidationError("用例编号必须是 JSON 数组") from exc
        if not isinstance(parsed, list):
            raise serializers.ValidationError("用例编号必须是 JSON 数组")
        ids: list[str] = []
        for item in parsed:
            if not isinstance(item, (str, int)):
                raise serializers.ValidationError("用例编号必须是字符串")
            clean = str(item).strip()
            if clean:
                ids.append(clean)
        return ids

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
