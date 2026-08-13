"""Shared DRF renderers — enforce the project-wide response envelope.

By default DRF returns bare JSON; the frontend api-client expects every
response to follow the ``{status, data}`` convention defined in
``frontend/src/shared/api-client.ts`` (``DjangoResponse<T>``).

``EnvelopeJSONRenderer`` wraps all successful (2xx) responses in this
envelope.  Errors (4xx/5xx) are left unwrapped so DRF's built-in error
format (``{detail: ...}`` or field-level errors) is preserved, which the
frontend's ``formatApiError()`` already understands.
"""

from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    """JSON renderer that wraps successful responses in ``{status, data}``.

    Set as the default renderer in ``REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]``
    to apply project-wide.  Individual ViewSets can override per-view if needed.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # Error responses keep DRF's native format (the frontend already
        # understands it via formatApiError).
        if response is not None and response.status_code >= 400:
            wrapped = {"status": False, "message": _extract_message(data)}
            if isinstance(data, dict) and "retry" in data:
                wrapped["retry"] = bool(data["retry"])
        else:
            wrapped = {"status": True, "data": data}

        return super().render(wrapped, accepted_media_type, renderer_context)


def _extract_message(data) -> str:
    """Pull a user-facing message from a DRF error response."""
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, str):
            if detail.startswith("JSON parse error"):
                return "请求格式错误"
            return detail
        # Field-level errors — return first field's first error
        for field, errors in data.items():
            if isinstance(errors, list) and errors:
                return str(errors[0])
    if isinstance(data, list):
        return str(data[0]) if data else "请求无效"
    return str(data) if data else "请求无效"
