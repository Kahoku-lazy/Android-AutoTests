from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        if response is not None and response.status_code >= 400:
            wrapped = {"status": False, "message": _extract_message(data)}
            if isinstance(data, dict) and "retry" in data:
                wrapped["retry"] = bool(data["retry"])
            if isinstance(data, dict) and data.get("code"):
                wrapped["code"] = data["code"]
        else:
            wrapped = {"status": True, "data": data}

        return super().render(wrapped, accepted_media_type, renderer_context)


def _extract_message(data) -> str:
    if isinstance(data, dict):
        message = data.get("message")
        if isinstance(message, str):
            return message
        detail = data.get("detail")
        if isinstance(detail, str):
            if detail.startswith("JSON parse error"):
                return "请求格式错误"
            return detail
        for field, errors in data.items():
            if isinstance(errors, list) and errors:
                return str(errors[0])
    if isinstance(data, list):
        return str(data[0]) if data else "请求无效"
    return str(data) if data else "请求无效"
