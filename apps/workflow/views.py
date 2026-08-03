"""workflow HTTP — /api/workflow/*"""

import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api as wf_api


def _body(request) -> dict:
    if not request.body:
        return {}
    return json.loads(request.body)


def directory_list(request):
    """GET /api/workflow/directories — flat + tree."""
    if request.method != "GET":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    return JsonResponse(
        {
            "ok": True,
            "directories": wf_api.list_directories_flat(),
            "tree": wf_api.get_directory_tree(),
        }
    )


@csrf_exempt
def directory_create(request):
    """POST /api/workflow/directories/create"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = _body(request)
    ok, result = wf_api.create_directory(
        name=data.get("name", ""),
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order", 0),
    )
    if ok:
        return JsonResponse({"ok": True, "directory": result}, status=201)
    return JsonResponse({"ok": False, "error": result}, status=400)


@csrf_exempt
def directory_detail(request, dir_id: int):
    """POST action=update|delete"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = _body(request)
    action = data.get("action", "update")
    if action == "delete":
        ok, result = wf_api.delete_directory(dir_id)
        if ok:
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "error": result}, status=400)
    ok, result = wf_api.update_directory(
        dir_id,
        name=data.get("name"),
        parent_id=data.get("parent_id"),
    )
    if ok:
        return JsonResponse({"ok": True, "directory": result})
    return JsonResponse({"ok": False, "error": result}, status=400)


def documents_list(request):
    """GET /api/workflow/documents?directory_id=&doc_type="""
    if request.method != "GET":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    directory_id = request.GET.get("directory_id")
    doc_type = request.GET.get("doc_type") or None
    dir_pk = int(directory_id) if directory_id and directory_id.isdigit() else None
    # directory_id= null means all; special all=1 for orphans too (default)
    docs = wf_api.list_documents(directory_id=dir_pk, doc_type=doc_type)
    return JsonResponse({"ok": True, "documents": docs})


@csrf_exempt
def documents_create(request):
    """POST /api/workflow/documents — 创建或更新（传 doc_id 且存在则更新）."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = _body(request)
    ok, result, status = wf_api.upsert_document(
        doc_id=data.get("doc_id") or None,
        title=data.get("title") or data.get("name") or "",
        doc_type=data.get("doc_type") or "",
        config=data.get("config"),
        directory_id=data.get("directory_id"),
        description=data.get("description") or "",
    )
    if ok:
        return JsonResponse({"ok": True, "document": result}, status=status)
    return JsonResponse({"ok": False, "error": result}, status=status)


@csrf_exempt
def document_detail(request, doc_id: str):
    """GET / PUT / DELETE /api/workflow/documents/<doc_id>"""
    if request.method == "GET":
        doc = wf_api.get_document(doc_id)
        if not doc:
            return JsonResponse({"ok": False, "error": "文档不存在"}, status=404)
        return JsonResponse({"ok": True, "document": doc})

    if request.method == "PUT":
        data = _body(request)
        existing = wf_api.get_document(doc_id)
        if not existing:
            return JsonResponse({"ok": False, "error": "文档不存在"}, status=404)
        clear_dir = False
        if "directory_id" in data:
            dir_id = data.get("directory_id")
            clear_dir = dir_id is None or dir_id == ""
            directory_id = None if clear_dir else dir_id
        else:
            directory_id = existing.get("directory_id")
        ok, result, status = wf_api.upsert_document(
            doc_id=doc_id,
            title=data.get("title") or existing["title"],
            doc_type=data.get("doc_type") or existing["doc_type"],
            config=data.get("config") if "config" in data else existing["config"],
            directory_id=directory_id,
            description=data.get("description", existing.get("description") or ""),
            allow_create=False,
            clear_directory=clear_dir,
        )
        if ok:
            return JsonResponse({"ok": True, "document": result})
        return JsonResponse({"ok": False, "error": result}, status=status)

    if request.method == "DELETE":
        ok, err = wf_api.delete_document(doc_id)
        if ok:
            return JsonResponse({"ok": True})
        return JsonResponse({"ok": False, "error": err}, status=404)

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def documents_import(request):
    """POST /api/workflow/documents/import  body=envelope JSON, ?overwrite=1"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = _body(request)
    overwrite = request.GET.get("overwrite") in ("1", "true", "True") or bool(data.get("overwrite"))
    # 允许 { envelope: {...} } 或直接 envelope
    payload = data.get("envelope") if isinstance(data.get("envelope"), dict) else data
    ok, result, status = wf_api.import_document_envelope(payload, overwrite=overwrite)
    if ok:
        return JsonResponse({"ok": True, "document": result}, status=status)
    return JsonResponse({"ok": False, "error": result}, status=status)


@csrf_exempt
def document_move(request, doc_id: str):
    """POST /api/workflow/documents/<doc_id>/move  { directory_id }"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = _body(request)
    raw = data.get("directory_id", data.get("parent_id"))
    dir_id = None if raw in (None, "", "null") else int(raw)
    ok, result = wf_api.move_document(doc_id, dir_id)
    if ok:
        return JsonResponse({"ok": True, "document": result})
    return JsonResponse({"ok": False, "error": result}, status=400)


@csrf_exempt
def directory_move(request, dir_id: int):
    """POST /api/workflow/directories/<id>/move  { parent_id }"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = _body(request)
    raw = data.get("parent_id")
    parent_id = None if raw in (None, "", "null") else int(raw)
    ok, result = wf_api.move_directory(dir_id, parent_id)
    if ok:
        return JsonResponse({"ok": True, "directory": result})
    return JsonResponse({"ok": False, "error": result}, status=400)


def document_export(request, doc_id: str):
    """GET /api/workflow/documents/<doc_id>/export?download=1"""
    if request.method != "GET":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    ok, result = wf_api.export_document(doc_id)
    if not ok:
        return JsonResponse({"ok": False, "error": result}, status=404)
    if request.GET.get("download") in ("1", "true", "True"):
        body = json.dumps(result, ensure_ascii=False, indent=2)
        resp = HttpResponse(body, content_type="application/json; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{doc_id}.json"'
        return resp
    return JsonResponse({"ok": True, "envelope": result})
