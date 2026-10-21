"""ai-assistant avatar upload — POST /api/ai/upload-avatar/."""

import base64

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView


class UploadAvatarAPIView(APIView):
    """POST /api/ai/upload-avatar — base64 头像 → data URI。"""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
    def post(self, request):
        img_b64 = request.data.get("image") or ""
        if not img_b64:
            raise ValidationError("no image data")
        # Normalise: strip the data: prefix if present, so we can prepend our own
        if "," in img_b64:
            img_b64 = img_b64.split(",", 1)[1]
        # Validate that it's actually decodable base64
        try:
            base64.b64decode(img_b64)
        except Exception:
            raise ValidationError("头像上传失败，请重试")
        data_uri = f"data:image/png;base64,{img_b64}"
        return Response({"url": data_uri})
