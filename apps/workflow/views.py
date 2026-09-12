"""workflow HTTP — /api/workflow/*（legacy 平铺信封）."""

import json

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import api as wf_api


def _body(request) -> dict:
    if not request.body:
        return {}
    return json.loads(request.body)


def _prototype_id(request, data: dict | None = None):
    raw = None
    if data is not None:
        raw = data.get("prototype_id")
    if raw in (None, ""):
        raw = request.GET.get("prototype_id")
    if raw in (None, "", "null"):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def prototypes_list(request):
    """GET /api/workflow/prototypes — 列表."""
    if request.method != "GET":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    return JsonResponse({"status": True, "prototypes": wf_api.list_prototypes()})


@csrf_exempt
def prototypes_create(request):
    """POST /api/workflow/prototypes/create"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    ok, result, status = wf_api.create_prototype(
        name=data.get("name", ""),
        description=data.get("description") or "",
    )
    if ok:
        return JsonResponse({"status": True, "prototype": result}, status=status)
    return JsonResponse({"status": False, "message": result}, status=status)


@csrf_exempt
def prototype_detail(request, prototype_id: int):
    """GET / PUT|PATCH / DELETE /api/workflow/prototypes/<id>"""
    if request.method == "GET":
        proto = wf_api.get_prototype(prototype_id)
        if not proto:
            return JsonResponse({"status": False, "message": "原型不存在"}, status=404)
        return JsonResponse({"status": True, "prototype": proto})

    if request.method in ("PUT", "PATCH", "POST"):
        data = _body(request)
        action = data.get("action")
        if action == "delete" or request.method == "DELETE":
            ok, result, status = wf_api.delete_prototype(prototype_id)
            if ok:
                return JsonResponse({"status": True})
            return JsonResponse({"status": False, "message": result}, status=status)
        ok, result, status = wf_api.update_prototype(
            prototype_id,
            name=data.get("name"),
            description=data.get("description"),
        )
        if ok:
            return JsonResponse({"status": True, "prototype": result})
        return JsonResponse({"status": False, "message": result}, status=status)

    if request.method == "DELETE":
        ok, result, status = wf_api.delete_prototype(prototype_id)
        if ok:
            return JsonResponse({"status": True})
        return JsonResponse({"status": False, "message": result}, status=status)

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


def directory_list(request):
    """GET /api/workflow/directories?prototype_id= — flat + tree."""
    if request.method != "GET":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    proto_id = _prototype_id(request)
    return JsonResponse(
        {
            "status": True,
            "directories": wf_api.list_directories_flat(prototype_id=proto_id),
            "tree": wf_api.get_directory_tree(prototype_id=proto_id),
        }
    )


@csrf_exempt
def directory_create(request):
    """POST /api/workflow/directories/create"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    ok, result = wf_api.create_directory(
        name=data.get("name", ""),
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order", 0),
        prototype_id=_prototype_id(request, data),
    )
    if ok:
        return JsonResponse({"status": True, "directory": result}, status=201)
    return JsonResponse({"status": False, "message": result}, status=400)


@csrf_exempt
def directory_detail(request, dir_id: int):
    """POST action=update|delete"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    action = data.get("action", "update")
    if action == "delete":
        ok, result = wf_api.delete_directory(dir_id)
        if ok:
            return JsonResponse({"status": True})
        return JsonResponse({"status": False, "message": result}, status=400)
    ok, result = wf_api.update_directory(
        dir_id,
        name=data.get("name"),
        parent_id=data.get("parent_id"),
    )
    if ok:
        return JsonResponse({"status": True, "directory": result})
    return JsonResponse({"status": False, "message": result}, status=400)


def documents_list(request):
    """GET /api/workflow/documents?prototype_id=&directory_id=&doc_type="""
    if request.method != "GET":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    directory_id = request.GET.get("directory_id")
    doc_type = request.GET.get("doc_type") or None
    dir_pk = int(directory_id) if directory_id and directory_id.isdigit() else None
    docs = wf_api.list_documents(
        prototype_id=_prototype_id(request),
        directory_id=dir_pk,
        doc_type=doc_type,
    )
    return JsonResponse({"status": True, "documents": docs})


@csrf_exempt
def documents_create(request):
    """POST /api/workflow/documents — 创建或更新（传 doc_id 且存在则更新）."""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    ok, result, status = wf_api.upsert_document(
        doc_id=data.get("doc_id") or None,
        title=data.get("title") or data.get("name") or "",
        doc_type=data.get("doc_type") or "",
        config=data.get("config"),
        directory_id=data.get("directory_id"),
        description=data.get("description") or "",
        prototype_id=_prototype_id(request, data),
    )
    if ok:
        return JsonResponse({"status": True, "document": result}, status=status)
    return JsonResponse({"status": False, "message": result}, status=status)


@csrf_exempt
def document_detail(request, doc_id: str):
    """GET / PUT / DELETE /api/workflow/documents/<doc_id>"""
    if request.method == "GET":
        doc = wf_api.get_document(doc_id)
        if not doc:
            return JsonResponse({"status": False, "message": "文档不存在"}, status=404)
        return JsonResponse({"status": True, "document": doc})

    if request.method == "PUT":
        data = _body(request)
        existing = wf_api.get_document(doc_id)
        if not existing:
            return JsonResponse({"status": False, "message": "文档不存在"}, status=404)
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
            prototype_id=existing.get("prototype_id"),
        )
        if ok:
            return JsonResponse({"status": True, "document": result})
        return JsonResponse({"status": False, "message": result}, status=status)

    if request.method == "DELETE":
        ok, err = wf_api.delete_document(doc_id)
        if ok:
            return JsonResponse({"status": True})
        return JsonResponse({"status": False, "message": err}, status=404)

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


@csrf_exempt
def documents_import(request):
    """POST /api/workflow/documents/import  body=envelope JSON, ?overwrite=1"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    overwrite = request.GET.get("overwrite") in ("1", "true", "True") or bool(data.get("overwrite"))
    payload = data.get("envelope") if isinstance(data.get("envelope"), dict) else data
    if isinstance(payload, dict) and not payload.get("prototype_id"):
        pid = _prototype_id(request, data)
        if pid is not None:
            payload = {**payload, "prototype_id": pid}
    ok, result, status = wf_api.import_document_envelope(payload, overwrite=overwrite)
    if ok:
        return JsonResponse({"status": True, "document": result}, status=status)
    return JsonResponse({"status": False, "message": result}, status=status)


@csrf_exempt
def document_move(request, doc_id: str):
    """POST /api/workflow/documents/<doc_id>/move  { directory_id }"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    raw = data.get("directory_id", data.get("parent_id"))
    dir_id = None if raw in (None, "", "null") else int(raw)
    ok, result = wf_api.move_document(doc_id, dir_id)
    if ok:
        return JsonResponse({"status": True, "document": result})
    return JsonResponse({"status": False, "message": result}, status=400)


@csrf_exempt
def directory_move(request, dir_id: int):
    """POST /api/workflow/directories/<id>/move  { parent_id }"""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    data = _body(request)
    raw = data.get("parent_id")
    parent_id = None if raw in (None, "", "null") else int(raw)
    ok, result = wf_api.move_directory(dir_id, parent_id)
    if ok:
        return JsonResponse({"status": True, "directory": result})
    return JsonResponse({"status": False, "message": result}, status=400)


def document_export(request, doc_id: str):
    """GET /api/workflow/documents/<doc_id>/export?download=1"""
    if request.method != "GET":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    ok, result = wf_api.export_document(doc_id)
    if not ok:
        return JsonResponse({"status": False, "message": result}, status=404)
    if request.GET.get("download") in ("1", "true", "True"):
        body = json.dumps(result, ensure_ascii=False, indent=2)
        resp = HttpResponse(body, content_type="application/json; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{doc_id}.json"'
        return resp
    return JsonResponse({"status": True, "envelope": result})
