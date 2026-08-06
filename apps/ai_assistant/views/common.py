"""Shared helpers for ai-assistant view modules."""

from django.http import JsonResponse


def validation_error(errors: dict, status: int = 400):
    return JsonResponse(
        {
            "status": False,
            "message": "; ".join(f"{k}: {v}" for k, v in errors.items()),
            "errors": errors,
        },
        status=status,
    )
